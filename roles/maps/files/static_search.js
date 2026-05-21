// Original (MIT Licensed): https://github.com/jacopofar/static-osm-indexer/

// Remove diacritics for search
function cleanForMatch(str, debug=false) {
  return str
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/'/g, "")
    .toLowerCase()
}

var AddressTextualIndex = class {
  constructor({baseURL, fetcher, cacheKey, map}) {

    // set by self.init() (aka self.initializer). Searches await for these to be set.
    this.stopWords = /* @__PURE__ */ new Set();
    this.minLength = 3;
    this.numCities = null

    // constant
    this.tokenRegex = /[^\p{L}|^\p{N}]+/u;
    this.baseURL = baseURL;
    this.fetcher = fetcher || (
      url => fetch(url + "?" + encodeURI(cacheKey || ""))
    )
    this.map = map
    this.initializer = this.init();

    // Changes potentially per-query. However, 1) they change together (i.e.
    // are consistent with each other) and 2) they are merely used as a cache.
    // If there's a race condition, it will at worst make an extra request.
    this.currentFileToken = null;
    this.currentFileContent = [];

    // Incremented at the beginning of each query (before any `await`s) to
    // resolve race conditions later in the query.
    this.lastQueryId = 0

    // Change potentially per-query. It happens after an `await`, and only if
    // it is during the last search.
    this.lastFileTokenLength = null
  }
  async init() {
    const data = await (await this.fetcher(`${this.baseURL}/index_metadata.json`)).json();
    this.stopWords = new Set(data.stopwords);
    this.minLength = data.token_length;
    this.numCities = Number(data.num_cities) || 163042;
  }
  async fileSearch(queryTokens) {
    let results = [];
    if (this.debugFlags.candidateTokens) {
      this.debugOut.candidateTokens = {}
    }
    for (let candidate of this.currentFileContent) {
      const candidateString = `${candidate.name} ${candidate.admin1 || ""} ${candidate.country}`
      const candidateTokens = cleanForMatch(candidateString).split(this.tokenRegex)
      if (this.debugFlags.candidateTokens) { // expensive, so don't do this regularly
        this.debugOut.candidateTokens[candidateString] = candidateTokens
      }
      const everyQueryTokenMatchesSomething = queryTokens.every((qt) => {
        return candidateTokens.some((candidateToken) => candidateToken.startsWith(qt));
      })
      if (everyQueryTokenMatchesSomething) {
        results.push(candidate);
      }
    }
    const mapCenter = this.map.getCenter()
    const get_lat = p => Number(p.lat)
    const get_lng = p => {
        let lng = Number(p.lon)

        // Longitude wraps around the world. Let's minimize the
        // distance between the location and the map center.
        //
        // For instance, if mapCenter.lng is 179 and p.lon is -179,
        // let's represent p.lon as 181. That way the difference is 2
        // instead of 358, and we get a useful distance.
        if (lng - mapCenter.lng > 180) {
            lng = lng - 360
        } else if (lng - mapCenter.lng < -180) {
            lng = lng + 360
        }

        return lng
    }
    const cleanedQuery = queryTokens.join(' ')
    const this_ = this
    function getSortScore(item) {
      // We want any city with an order of magnitude population larger to show up first
      // log(0) is -Infinity so we'll set a minimum population of 1
      const pop_factor = Math.log10(Number(item.pop) || 1)

      // Within an order of magnitude, we'd like closer things to show up first
      // This is basically log10(distance^2 + 1)
      // Using a log because the difference matters less as we get further
      const dist_factor = - Math.log10(1 + (
        (get_lat(item) - mapCenter.lat) ** 2 +
        (get_lng(item) - mapCenter.lng) ** 2
      )) / 1.4 // experimentally tuned with tests

      const exact_match_factor = (
        // Just bigger than the highest population factor, until we get to 100M cities
        cleanedQuery.includes(cleanForMatch(item.name).split(this_.tokenRegex).join(' ')) * 8 +

        // I'm not even sure if we care about these
        (
          Boolean(item.admin1) && // don't give points for "matching" an empty string
          cleanedQuery.includes(cleanForMatch(item.admin1 || '').split(this_.tokenRegex).join(' '))
        ) * 2 +
        cleanedQuery.includes(cleanForMatch(item.country).split(this_.tokenRegex).join(' ')) * 2
      )

      if (this_.debugFlags.sorting) {
        this_.debugOut.sortFactors[`${item.name}...${item.admin1 || ""}...${item.country}...${item.pop || 0}...${item.lat}...${item.lon}`] = {pop_factor, dist_factor, exact_match_factor}
      }

      return pop_factor + dist_factor + exact_match_factor
    }
    for (const x of results) {
      x.sortScore = getSortScore(x)
    }
    results.sort((x, y) => {
        return y.sortScore - x.sortScore
    })
    return results;
  }
  async search(query, debugFlags = null) {
    // mitigate race conditions below
    this.lastQueryId++
    const thisQueryId = this.lastQueryId

    this.debugFlags = debugFlags || {}

    this.debugOut = {
      // For debugging purposes, we want to know the last file token that was
      // used, even if it was null. So, we'd want something that's reset to
      // null for every request. However, this.currentFileToken sticks around
      // along with this.currentFileContent because subsequent queries will
      // probably use it. We lose that benefit if we reset it to null at the
      // beginning of each request.
      //
      // So, we have this.debugOut.lastFileToken instead that we reset to null.
      lastFileToken: null,

      sortFactors: {}
    };

    if (this.debugFlags.matching) {
      console.log('query:', query)
    }
    await this.initializer;
    const queryTokens = cleanForMatch(query).split(this.tokenRegex);
    if (this.debugFlags.queryTokens) {
      this.debugOut.queryTokens = queryTokens
    }
    // The files we return will be named `${fileToken}.json`. In the basic case, `fileToken` is
    // determined by truncating the first sufficiently long token in `queryTokens` to
    // `this.minLength` characters. Anything you type after that will be searched for within
    // `${fileToken}.json`. For instance, "new york" gives us `new.json`. "ne york" gives us
    // `yor.json`.
    //
    // However, if there is no token long enough in `queryTokens`, we take the longest token
    // available. If there are multiple tokens of the maximum length, we again take the first one.
    // So, we first set `this.fileTokenLength` to be the minimum of `this.minLength` and the length
    // of longest token, and then we find the first token of that length.
    //
    // This leads to a couple interesting modes for these "short token" json files. Most
    // importantly, it allows us to search for names that are shorter than `this.minLength`.
    // Secondly, it allows us to search for very popular items with only a couple characters.
    // Take the following as an idea, it's not necessarily what we're going with at least not yet:
    //
    // For instance, if the user types in "ne" we could return `ne.json` and show them
    // "New York City" and 9 other "top results". If the user types "ne " (with a space,
    // indicating that "ne" is the whole word) they might get something like "Ne Byaw" and
    // "Mui Ne". If they go on to type "ne by" it will filter down to "Ne Byaw". But if they
    // instead go on to type "ne plymouth", now we have the token "plymouth" which is longer
    // than "ne" so we return `ply.json` which contains "New Plymouth" which will show up in
    // their results.
    //
    // So, "short token" json files can probably get away with containing only 1) ten "top
    // results" entries and 2) all entries with that short token as a whole word.
    //
    // A downside is that if the user types "ne ply" they might get something rare like
    // "New Plymouth" but if they just type "ne pl" they will not since "New Plymouth" is
    // not a "top result" in ne.json. This could lead to confusion, and this is an open
    // question. Perhaps the user would understand that they should not be relying on
    // partial words this way. Or perhaps we could put in a "add more characters"
    // notification if there are no results for "ne pl".
    const fileTokenLength = (Math.min(
      this.minLength,
      Math.max(...queryTokens.map(p => p.length)),
    ))

    // We want this to be set on the last search the user did. We want to avoid a race
    // condition from two concurrent queries getting here of order. We set `this.lastQueryId`
    // before any `await`s to make sure it indeed corresponds to the last search.
    // (the geocoder library uses a debouncer to prevent too-frequent queries
    // but I don't think it prevents concurrent queries)
    //
    // Though FWIW the only `await` above here is waiting on the same event (`this.initializer`),
    // so perhaps that means they won't get hre out of order, but I'm not sure.
    if (this.lastQueryId === thisQueryId) {
        this.lastFileTokenLength = fileTokenLength
    }

    for (let p of queryTokens) {
      if (p.length < fileTokenLength || this.stopWords.has(p)) {
        continue;
      }
      const fileToken = p.substring(0, fileTokenLength);
      if (this.debugFlags.matching) {
        console.log('fileToken (trying for each word):', fileToken)
      }
      if (this.currentFileToken === fileToken) {
        this.debugOut.lastFileToken = this.currentFileToken;
        return this.fileSearch(queryTokens);
      } else {
        const response = await this.fetcher(
          `${this.baseURL}/${fileToken}.json`
        );
        let data = [];
        if (response.ok) {
          data = await response.json();
        } else {
          data = [];
        }
        this.currentFileToken = fileToken;
        this.currentFileContent = data;
        this.debugOut.lastFileToken = this.currentFileToken;
        return this.fileSearch(queryTokens);
      }
    }
    throw new Error("Query string insufficient for the search");
  }

  // Called after results are given
  lastQueryWasPartial() {
    // Return whether there might be more results on the *last initiated* search if
    // the user keeps typing. I.e., if they only typed a couple characters and the
    // json file they're searching within doesn't contain as much as the json file
    // they would get if they typed a longer query. This is used to avoid showing
    // "No Results Found" prematurely.
    return this.lastFileTokenLength < this.minLength
  }
};
export {
  AddressTextualIndex
};
