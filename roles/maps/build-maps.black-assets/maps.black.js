import maplibregl from 'maplibre-gl'
import maplibreglstyles from 'maplibre-gl/dist/maplibre-gl.css'
import { Protocol as PMTilesProtocol, PMTiles } from 'pmtiles'
import rtlPlugin from './mapbox-gl-rtl-text.js.bin'
import MaplibreInspect from '@maplibre/maplibre-gl-inspect'
import inspectstyles from '@maplibre/maplibre-gl-inspect/dist/maplibre-gl-inspect.css';

import { ShieldRenderer, transposeImageData } from "@americana/maplibre-shield-generator";

// TODO: Will be core feature in https://github.com/maplibre/maplibre-style-spec/issues/583, use that instead of plugin then.
import mlcontour from 'maplibre-contour'

if (maplibregl.getRTLTextPluginStatus() !== 'loaded') maplibregl.setRTLTextPlugin(URL.createObjectURL(new Blob([rtlPlugin], { type: "application/javascript" })), false)
// Defined by esbuild, mbtiles takes about 1.7mb. Should only be used for preview purposes probably
if (mbtiles) await import('./mbtiles.js').then(({ addMbtilesProtocol }) => addMbtilesProtocol(maplibregl))

maplibregl.addProtocol("pmtiles", (new PMTilesProtocol()).tile)

const mapComponents = {}
const pmtileresourcesProviders = {}
const pmtileresourcesMeta = {}

const checkAttribution = (mapid) => {
  if (!mapComponents[mapid].attributions) {
    mapComponents[mapid].attributions = new maplibregl.AttributionControl({ compact: !mapComponents[mapid].mapstyle.includes('openstreetmap') })
    mapComponents[mapid].attributions.onAdd = (e) => {
      const details = document.createElement('details')
      mapComponents[mapid].attributions._container = details
      details.open = mapComponents[mapid].mapstyle.includes('openstreetmap')
      details.classList.add('maplibregl-ctrl', 'maplibregl-ctrl-attrib', 'maplibregl-compact', 'maplibregl-compact-show')
      const summary = document.createElement('summary')
      summary.classList.add('maplibregl-ctrl-attrib-button')
      details.appendChild(summary)
      const textElem = document.createElement('div')
      textElem.classList.add('maplibregl-ctrl-attrib-inner')
      details.appendChild(textElem)
      if (mapComponents[mapid].mapstyle.includes('openstreetmap')) {
        const osmLink = document.createElement('a')
        osmLink.setAttribute('href', 'https://www.openstreetmap.org/copyright')
        osmLink.setAttribute('target', '_blank')
        osmLink.innerText = '© OpenStreetMap'
        textElem.append(osmLink)
      }
      const otherAttributions = document.createElement('a')
      otherAttributions.setAttribute('href', '#attribution')
      otherAttributions.innerText = 'Attributions'
      otherAttributions.onclick = async e => {
        e.preventDefault()
        mapComponents[mapid].shadowRoot.querySelector('.attributions').replaceChildren(...(await Promise.all(Object.keys(mapComponents[mapid].licenses).map(async k => {
          const localelem = document.createElement('li')
          const details = document.createElement('details')
          details.open = true
          const summary = document.createElement('summary')
          summary.append(k)

          const childelem = document.createElement('ul')
          childelem.append(...(await Promise.all(Object.keys(mapComponents[mapid].licenses[k]).map(async l => {
            const li = document.createElement('li')
            const details = document.createElement('details')
            const summary = document.createElement('summary')
            const code = document.createElement('code')
            const pre = document.createElement('pre')
            code.innerText = await mapComponents[mapid].licenses[k][l]
            pre.append(code)
            summary.append(l)
            details.append(summary, pre)
            li.append(details)
            return li
          }))))
          details.append(summary, childelem)
          localelem.append(details)
          return localelem
        }))))
        mapComponents[mapid].shadowRoot.querySelector('.attributionPopup').style.display = 'flex'
      }
      if (textElem.innerText.length) {
        textElem.append(' | ')
      }
      textElem.append(otherAttributions)
      return details
    }
    mapComponents[mapid].attributions.onRemove = (e) => {
      mapComponents[mapid].attributions._container.parentNode.removeChild(mapComponents[mapid].attributions._container)
    }
  }
  if ((mapComponents[mapid].requireAttribution === true || mapComponents[mapid].attribution === 'generous') && !mapComponents[mapid].map.hasControl(mapComponents[mapid].attributions)) {
    mapComponents[mapid].map.addControl(mapComponents[mapid].attributions)
  } else if (!(mapComponents[mapid].requireAttribution === true || mapComponents[mapid].attribution === 'generous') && mapComponents[mapid].map.hasControl(mapComponents[mapid].attributions)) {
    mapComponents[mapid].map.removeControl(mapComponents[mapid].attributions)
  }
}

// Stats for fonttiles for why selecting z21
// Noto sans max: 65280
// Max unicode code point: 1114112
//                    z21: 2097152

// TODO: Clean this up. Separate into two handlers and break out handling of languages, etc.
const resourcesHandler = async (params, abortController) => {
  const url = new URL(params.url)
  const protocol = url.protocol
  let mapid, inArchivePath, metadata, provider, inArchiveUrl, path
  if (protocol === 'relativeresources:') {
    const _inArchivePath = url.toString().replace('relativeresources://', '')
    inArchiveUrl = new URL(_inArchivePath, 'http://throwaway.local')
    inArchivePath = inArchiveUrl.pathname.replace('/', '')
    mapid = inArchiveUrl.searchParams.get('mapid')
  } else if (protocol === 'pmtileresources:') {
    const [_path, _inArchivePath] = url.toString().replace('pmtileresources://', '').split('.pmtiles/')
    path = _path
    inArchiveUrl = new URL(_inArchivePath, 'http://throwaway.local')
    mapid = inArchiveUrl.searchParams.get('mapid')
    inArchivePath = decodeURIComponent(inArchiveUrl.pathname.replace('/', ''))
    const pmtileresourcesUrl = new URL(path + '.pmtiles', mapComponents[mapid].baseurl).toString()
    provider = pmtileresourcesProviders[path] || (pmtileresourcesProviders[path] = new PMTiles(pmtileresourcesUrl))
    metadata = pmtileresourcesMeta[path] || (pmtileresourcesMeta[path] = JSON.parse(new TextDecoder().decode((await provider.getZxy(0, 0, 0)).data)))
  } else {
    throw new Error('Unsupported protocol')
  }
  mapComponents[mapid].licenses = mapComponents[mapid].licenses || { data: {}, styles: {}, fonts: {} }

  // Fonts are special and stored based on glyph number
  if (inArchivePath.startsWith('fonts')) {
    const [path, stack, filename] = inArchivePath.split('/')
    let results = []
    for (const font of stack.split(',')) {
      try {
        let res
        if (protocol === 'relativeresources:') {
          const _res = await fetch(new URL(`${path}/${font}/${filename}`, mapComponents[mapid].baseurl)).then(res => res.arrayBuffer())
          res = { data: _res }
          // This is not awaited to not block loading of the actual font
          if (!mapComponents[mapid].licenses.fonts[font]) mapComponents[mapid].licenses.fonts[font] = fetch(new URL(`${path}/${font}/LICENSE.txt`, mapComponents[mapid].baseurl)).then(res => res.text())
        } else if (protocol === 'pmtileresources:') {
          const index = metadata.fonts.indexOf(font)
          if (index === -1) continue
          const [tileIndex] = filename.split('-')
          // This is not awaited to not block loading of the actual font
          if (!mapComponents[mapid].licenses.fonts[font]) mapComponents[mapid].licenses.fonts[font] = provider.getZxy(20, index, 0).then(({ data }) => new TextDecoder().decode(data))
          res = await provider.getZxy(21, index, tileIndex)
        }
        results.push(res)
        // 48 is chosen arbitrarily to guess what a empty font tile is
        if (res.data.byteLength > 48) {
          return res
        }
      } catch (e) { }
    }
    // None seemed like an obvious match based on bytelength, return the largest
    return results.sort((a, b) => a.data.byteLength - b.data.byteLength)[0]
  }
  let fileIndex
  if (protocol === 'pmtileresources:') {
    fileIndex = metadata.files.indexOf(inArchivePath)
    if (fileIndex === -1) throw new Error('Resource not available in archive: ' + inArchivePath)
  }
  if (params.type === 'json') {
    if (inArchivePath.endsWith('style.json')) {
      if (protocol === 'relativeresources:') {
        mapComponents[mapid].licenses.styles[inArchivePath] = fetch(new URL(inArchivePath.replace('style.json', 'LICENSE.txt'), mapComponents[mapid].baseurl)).then(res => res.text())
      } else if (protocol === 'pmtileresources:') {
        const licenseIndex = metadata.files.indexOf(inArchivePath.replace('style.json', 'LICENSE.txt'))
        if (licenseIndex !== -1) {
          // This is not awaited to not block loading of the actual style
          mapComponents[mapid].licenses.styles[inArchivePath] = provider.getZxy(19, 0, licenseIndex).then(res => new TextDecoder().decode(res.data))
        }
      }
    }
    let data
    if (protocol === 'relativeresources:') {
      data = await fetch(new URL(inArchivePath, mapComponents[mapid].baseurl)).then(res => res.json())
    } else if (protocol === 'pmtileresources:') {
      data = JSON.parse(new TextDecoder().decode((await provider.getZxy(19, 0, fileIndex)).data))
    }

    if (data.sources) {
      if (mapComponents[mapid].globe) {
        data.projection = {
          type: 'globe'
        }
      }
      const terrarium = { type: "raster-dem", url: `pmtiles://${new URL('terrarium-z0-z10.pmtiles', mapComponents[mapid].baseurl)}`, tileSize: 256, maxzoom: 10 }
      if (protocol === 'relativeresources:') {
        delete terrarium.url
        terrarium.tiles = [new URL('terrarium/{z}/{x}/{y}.png', mapComponents[mapid].baseurl).toString().replace(/%7B/g, "{").replace(/%7D/g, "}")]
        terrarium.maxzoom = 13
      }
      if (mapComponents[mapid].terrain) {
        data.sources.terrarium = terrarium
        data.terrain = { "source": "terrarium", "exaggeration": 0.05 }
      }
      if (mapComponents[mapid].hillshade) {
        data.sources.hillshade = terrarium
        data.layers.splice(3, 0, {
          id: "hillshade",
          type: 'hillshade',
          source: "hillshade",
          "source-layer": "hillshade",
          layout: { visibility: 'visible' },
          minzoom: 8,
          paint: {
            "hillshade-shadow-color": "hsl(39, 21%, 33%)",
            "hillshade-illumination-direction": 315,
            "hillshade-exaggeration": 0.05
          }
        })
      }
      if (mapComponents[mapid].contours) {
        const contourOptions = {
          ...terrarium,
          worker: true, // offload isoline computation to a web worker to reduce jank
          cacheSize: 100, // number of most-recent tiles to cache
          timeoutMs: 30000, // timeout on fetch requests
        }
        if (protocol === 'relativeresources:') {
          contourOptions.url = terrarium.tiles[0]
        }
        const demSource = new mlcontour.DemSource(contourOptions)
        demSource.setupMaplibre(maplibregl)
        data.sources.contours = {
          type: "vector",
          tiles: [
            demSource.contourProtocolUrl({
              multiplier: 1,
              thresholds: {
                // zoom: [minor, major]
                11: [200, 1000],
                12: [100, 500],
                14: [50, 200],
                15: [20, 100],
              },
              // optional, override vector tile parameters:
              contourLayer: "contours",
              elevationKey: "ele",
              levelKey: "level",
              extent: 4096,
              buffer: 1,
            }),
          ],
          maxzoom: 15,
        }
        data.layers.push({
          id: "contour-lines",
          type: "line",
          source: "contours",
          "source-layer": "contours",
          paint: {
            "line-color": "rgba(0,0,0, 50%)",
            // level = highest index in thresholds array the elevation is a multiple of
            "line-width": ["match", ["get", "level"], 1, 1, 0.5],
          },
        })
        data.layers.push({
          id: "contour-labels",
          type: "symbol",
          source: "contours",
          "source-layer": "contours",
          filter: [">", ["get", "level"], 0],
          layout: {
            "symbol-placement": "line",
            "text-size": 10,
            "text-field": [
              "concat",
              ["to-string", ["round", ["get", "ele"]]],
              "m, ",
              ["to-string", ["round", ["*", ["get", "ele"], 3.28084]]],
              "ft"
            ],
            "text-font": ["Noto Sans Regular"],
          },
          paint: {
            "text-halo-color": "white",
            "text-halo-width": 0,
          },
        })
      }
      Object.keys(data.sources).forEach(k => {
        let datakey = k
        if (k === 'terrarium' || k === 'hillshade' || k === 'contours') {
          mapComponents[mapid].requireAttribution = true
          checkAttribution(mapid)
          datakey = 'terrarium-z0-z10'
        } else if (k === 'terrarium-visual') {
          data.sources[k] = {
            ...terrarium,
            type: "raster"
          }
        } else if (
          k.startsWith('naturalearth') &&
          // TODO: Better way to check for the NE vectors
          !['naturalearth-openmaptiles', 'naturalearth-protomaps', 'naturalearth-shortbread'].includes(k)
        ) {
          data.sources[k] = { type: "raster", url: `pmtiles://${new URL(`${k}.pmtiles`, mapComponents[mapid].baseurl)}`, tileSize: 512, maxzoom: 6 }
          if (protocol === 'relativeresources:') {
            delete data.sources[k].url
            if (k.includes('WEBP')) {
              data.sources[k].tiles = [new URL(`${k}/{z}/{x}/{y}.webp`, mapComponents[mapid].baseurl).toString().replace(/%7B/g, "{").replace(/%7D/g, "}")]
            } else {
              data.sources[k].tiles = [new URL(`${k}/{z}/{x}/{y}.png`, mapComponents[mapid].baseurl).toString().replace(/%7B/g, "{").replace(/%7D/g, "}")]
            }
          }
        } else if (k.startsWith('s2maps')) {
          mapComponents[mapid].requireAttribution = true
          checkAttribution(mapid)
          data.sources[k] = { type: "raster", url: `pmtiles://${new URL(`${k}.pmtiles`, mapComponents[mapid].baseurl)}`, tileSize: 256, maxzoom: 13 }
          if (protocol === 'relativeresources:') {
            delete data.sources[k].url
            data.sources[k].tiles = [new URL(`${k}/{z}/{x}/{y}.jpg`, mapComponents[mapid].baseurl).toString().replace(/%7B/g, "{").replace(/%7D/g, "}")]
          }
        } else {
          if (!['naturalearth-protomaps', 'naturalearth-shortbread'].includes(k)) {
            mapComponents[mapid].requireAttribution = true
            checkAttribution(mapid)
          }
          data.sources[k] = { type: "vector", url: `pmtiles://${new URL(`${k}.pmtiles`, mapComponents[mapid].baseurl)}`, maxzoom: 14 }
          if (['naturalearth-openmaptiles', 'naturalearth-protomaps', 'naturalearth-shortbread'].includes(k)) {
            data.sources[k].maxzoom = 8
          }
          if (protocol === 'relativeresources:') {
            delete data.sources[k].url
            data.sources[k].tiles = [new URL(`${k}/{z}/{x}/{y}.pbf`, mapComponents[mapid].baseurl).toString().replace(/%7B/g, "{").replace(/%7D/g, "}")]
          }
        }
        if (protocol === 'relativeresources:') {
          if (!mapComponents[mapid].licenses.data[datakey]) {
            mapComponents[mapid].licenses.data[datakey] = fetch(new URL(`tilejson/${datakey}.LICENSE.txt`, mapComponents[mapid].baseurl)).then(res => res.text())
          }
        } else if (protocol === 'pmtileresources:') {
          const licenseIndex = metadata.files.indexOf(`tilejson/${datakey}.LICENSE.txt`)
          if (licenseIndex !== -1 && !mapComponents[mapid].licenses.data[datakey]) {
            mapComponents[mapid].licenses.data[datakey] = provider.getZxy(19, 0, licenseIndex).then(({ data }) => new TextDecoder().decode(data))
          }
        }
      })
    }
    if (data.layers) {
      let languageFields
      if (mapComponents[mapid].languagemode === 'both' || mapComponents[mapid].languagemode === 'translated') {
        languageFields = mapComponents[mapid].languages.split(',').map(l => ["get", `name:${l}`])
      }
      if (mapComponents[mapid].languagemode === 'local') {
        languageFields = []
      }

      data.layers = data.layers.map(l => {
        if (l.layout?.["text-field"] && [
          'poi_volcano_rank1',
          'poi_peak_rank1',
          'poi_saddle',
          'mountain_peak',
          "natural-point-label",
          "mountain-peak",
          "mountain-peaks-important",
          "mountain-peaks",
        ].includes(l.id)) {
          l.layout["text-field"] = [
            "case",
            ["has", "ele"],
            [
              "case",
              [
                "==",
                ["get", "name"],
                ["coalesce", ...languageFields, ["get", "name"]]
              ],
              [
                "concat",
                ["coalesce", ...languageFields, ["get", "name"]],
                "\n",
                ["to-string", ["round", ["get", "ele"]]],
                "m, ",
                ["to-string", ["round", ["*", ["get", "ele"], 3.28084]]],
                "ft"
              ],
              [
                "format",
                ["coalesce", ...languageFields, ["get", "name"]],
                {},
                "\n",
                {},
                ["get", "name"],
                { "font-scale": 0.8 },
                "\n",
                {},
                ["to-string", ["round", ["get", "ele"]]],
                {},
                "m, ",
                {},
                ["to-string", ["round", ["*", ["get", "ele"], 3.28084]]],
                {},
                "ft",
                {}
              ]
            ],
            [
              "case",
              [
                "==",
                ["get", "name"],
                ["coalesce", ...languageFields, ["get", "name"]]
              ],
              ["coalesce", ...languageFields, ["get", "name"]],
              [
                "format",
                ["coalesce", ...languageFields, ["get", "name"]],
                {},
                "\n",
                {},
                ["get", "name"],
                { "font-scale": 0.8 }
              ]
            ]
          ]
          if (mapComponents[mapid].languagemode === 'translated') {
            l.layout["text-field"] = [
              "case",
              ["all", ["has", "ele"]],
              [
                "concat",
                ["coalesce", ...languageFields],
                "\n",
                ["to-string", ["round", ["get", "ele"]]],
                "m, ",
                ["to-string", ["round", ["*", ["get", "ele"], 3.28084]]],
                "ft"
              ],
              ["coalesce", ...languageFields, ["get", "name"]]
            ]
          }
          return l
        }
        if (l.layout?.["text-field"] && ![
          'housenumber',
          'road_shield',
          'highway-shield-non-us',
          'highway-shield-us-interstate',
          'road_shield_us',
          'highway_name_motorway',
          'highway_ref',
          'highway-shield',
          'highway-shield-us-other',
          'highway-shield-tertiary',
          'highway-shield-secondary',
          'highway-shield-primary',
          'highway-shield-motorway',
          'airport_label',
          'airport_gate_label',
          'airport_gate',
          'label-motorway-shield',
          'contour-labels',
          'road-number-shield',
          'highway-shield-other',
          "highway_shield_other",
          "highway_shield_us_other",
          "highway_shield_us_interstate",
          "label-address-housenumber",
          "boundary_country_label_right",
          "boundary_country_label_left",
          "housenumbers",
          "airport_gate_label"
        ].includes(l.id)) {
          l.layout["text-field"] = [
            "case",
            ["==", ["get", "name"], ["coalesce", ...languageFields, ["get", "name"]]],
            ["coalesce", ...languageFields, ["get", "name"]],
            [
              "format",
              ["coalesce", ...languageFields, ["get", "name"]],
              {},
              "\n",
              {},
              ["get", "name"],
              { "font-scale": 0.8 }
            ]
          ]
          if (mapComponents[mapid].languagemode === 'translated') {
            l.layout["text-field"] = ["coalesce", ...languageFields]
          }
          return l
        }

        return l
      })
    }
    if (protocol === 'relativeresources:') {
      data.glyphs = `relativeresources://fonts-minimal/{fontstack}/{range}.pbf?mapid=${inArchiveUrl.searchParams.get('mapid')}`
      if (data.sprite && typeof data.sprite === 'string') data.sprite = `relativeresources:/${new URL(data.sprite, mapComponents[mapid].baseurl).pathname}?mapid=${inArchiveUrl.searchParams.get('mapid')}`
      if (data.sprite && Array.isArray(data.sprite)) {
        data.sprite.forEach(s => {
          s.url = `relativeresources:/${new URL(s.url, mapComponents[mapid].baseurl).pathname}?mapid=${inArchiveUrl.searchParams.get('mapid')}`
        })
      }
    } else if (protocol === 'pmtileresources:') {
      data.glyphs = `pmtileresources://${path}.pmtiles/fonts/{fontstack}/{range}.pbf?mapid=${inArchiveUrl.searchParams.get('mapid')}`
      if (data.sprite && typeof data.sprite === 'string') data.sprite = `pmtileresources://${path}.pmtiles${new URL(data.sprite, mapComponents[mapid].baseurl).pathname}?mapid=${inArchiveUrl.searchParams.get('mapid')}`
      if (data.sprite && Array.isArray(data.sprite)) {
        data.sprite.forEach(s => {
          s.url = `pmtileresources://${path}.pmtiles${new URL(s.url, mapComponents[mapid].baseurl).pathname}?mapid=${inArchiveUrl.searchParams.get('mapid')}`
        })
      }
    }

    return { data }
  }

  if (protocol === 'relativeresources:') {
    const res = await fetch(new URL(inArchivePath, mapComponents[mapid].baseurl)).then(res => res.arrayBuffer())
    if (params.type === 'image') {
      return { data: new Uint8ClampedArray(res) }
    }
    // Any non-font, non-json, non-image
    return { data: res }
  } else if (protocol === 'pmtileresources:') {
    if (params.type === 'image') {
      return { data: new Uint8ClampedArray((await provider.getZxy(19, 0, fileIndex)).data) }
    }
    // Any non-font, non-json, non-image
    return provider.getZxy(19, 0, fileIndex)
  }
}
maplibregl.addProtocol('pmtileresources', resourcesHandler)
maplibregl.addProtocol('relativeresources', resourcesHandler)

const maplib = async (mapcontainer, component) => {
  mapComponents[component.mapid] = component

  const inspectStyles = new CSSStyleSheet()
  inspectStyles.replaceSync(inspectstyles)
  component.shadowRoot.adoptedStyleSheets.unshift(inspectStyles)

  const maplibreStyles = new CSSStyleSheet()
  maplibreStyles.replaceSync(maplibreglstyles)
  component.shadowRoot.adoptedStyleSheets.unshift(maplibreStyles)

  const attributionPopup = document.createElement('div')
  const attributions = document.createElement('ul')
  attributions.classList.add('attributions')
  const attributionCloseLink = document.createElement('a')
  attributionCloseLink.classList.add('attributionCloseLink')
  attributionPopup.classList.add('attributionPopup')
  attributionCloseLink.onclick = (e) => {
    e.preventDefault()
    attributionPopup.style.display = 'none'
  }
  attributionCloseLink.innerText = '×'
  attributionCloseLink.href = '#'
  attributionCloseLink.ariaLabel = 'Close attributions'
  const attributionsHeader = document.createElement('h1')
  attributionsHeader.innerText = 'Licenses and attributions'
  attributionPopup.append(attributionCloseLink, attributionsHeader, attributions)
  component.shadowRoot.append(attributionPopup)

  let style
  if (component.mapstyleurl) style = component.mapstyleurl
  if (component.mapstylejson) style = component.mapstylejson
  if (!style) {
    component.mapstyle = component.mapstyle || 'openstreetmap-protomaps/protomaps/grayscale'
    if (component.loader === 'http') {
      const url = new URL(`relativeresources://styles/${component.mapstyle}/style.json`)
      url.searchParams.set('mapid', component.mapid)
      style = url.toString()
    } else if (component.loader === 'pmtiles') {
      const url = new URL(`pmtileresources://resourcetiles-minimal.pmtiles/styles/${component.mapstyle}/style.json`)
      url.searchParams.set('mapid', component.mapid)
      style = url.toString()
    }
  }

  const map = new maplibregl.Map({
    container: mapcontainer,
    zoom: component.zoom,
    center: [component.lon, component.lat],
    pitch: component.pitch,
    bearing: component.bearing,
    attributionControl: false,
    cooperativeGestures: component.cooperativegestures,
    // Required for screenshots
    // preserveDrawingBuffer: true,
    style
  })

  if (component.mapstyle.includes('americana')) {
    function missingIconHandler(
      shieldRenderer,
      map,
      e
    ) {
      try {
        missingIconLoader(shieldRenderer, map, e);
      } catch (err) {
        console.error(`Exception while loading image ‘${e?.id}’:\n`, err);
      }
    }

    function missingIconLoader(
      shieldRenderer,
      map,
      e
    ) {
      const sprite = e.id.split("\n")[1].split("=")[1];
      const color = e.id.split("\n")[2].split("=")[1];
      const sourceSprite = map.style.getImage(sprite);

      if (!sourceSprite) {
        console.error(`No such sprite ${sprite}`);
        return;
      }

      const width = sourceSprite.data.width;
      const height = sourceSprite.data.height;

      let ctx = shieldRenderer.createGraphics({
        width,
        height,
      });
      transposeImageData(ctx, sourceSprite, 0, false, color);

      if (ctx == null) {
        console.warn("Didn't produce an icon for", JSON.stringify(e.id));
        ctx = shieldRenderer.createGraphics({ width: 1, height: 1 });
      }

      const imgData = ctx.getImageData(
        0,
        0,
        ctx.canvas.width,
        ctx.canvas.height
      );
      map.addImage(
        e.id,
        {
          width: ctx.canvas.width,
          height: ctx.canvas.height,
          data: imgData.data,
        },
        {
          pixelRatio: shieldRenderer.pixelRatio(),
        }
      );
    }

    const orderedRouteAttributes = ["network", "ref", "name", "color"];

    function parseImageName(imageName) {
      let lines = imageName.split("\n");
      lines.shift(); // "shield"
      let parsed = Object.fromEntries(
        orderedRouteAttributes.map((a, i) => [a, lines[i]])
      );
      parsed.imageName = imageName;
      return parsed;
    }

    const routeParser = {
      parse: (id) => {
        return parseImageName(id);
      },
      format: (network, ref, name) =>
        `shield\n${network}\n${ref}\n${name}\n`,
    };

    // TODO: this is a temporary workaround, load over http if the http loader is used
    const notoSansCondensed = await resourcesHandler({
      url: 'pmtileresources://resourcetiles-minimal.pmtiles/styles/openstreetmap-openmaptiles/osm-americana/americana/Noto Sans Condensed.woff2?mapid=' + component.mapid,
    })

    const amaricanaFont = new CSSStyleSheet()
    amaricanaFont.replaceSync(`@font-face { font-family: "Noto Sans Condensed"; src: url(data:application/x-font-woff2;charset=utf-8;base64,${btoa(notoSansCondensed.data)}) format("woff2");}`)
    component.shadowRoot.adoptedStyleSheets.unshift(amaricanaFont)

    // TODO: this is a temporary workaround, load over http if the http loader is used
    const sheilds = await resourcesHandler({
      url: 'pmtileresources://resourcetiles-minimal.pmtiles/styles/openstreetmap-openmaptiles/osm-americana/americana/shields.json?mapid=' + component.mapid,
      type: 'json'
    })
    const shieldRenderer = new ShieldRenderer(sheilds.data, routeParser)
      .filterImageID(imageID => imageID && imageID.startsWith("shield"))
      .filterNetwork(network => !/^[lrni][chimpw]n$/.test(network))
      .renderOnMaplibreGL(map)

    map.on("styleimagemissing", function (e) {
      switch (e.id.split("\n")[0]) {
        case "shield":
          break;
        case "poi":
          missingIconHandler(shieldRenderer, map, e);
          break;
        default:
          console.warn("Image id not recognized:", JSON.stringify(e.id));
          break;
      }
    });
  }

  // Reflect state back to the component
  map.on('moveend', () => {
    component.ignoreCameraChanges = true
    component.zoom = map.getZoom()
    component.bearing = map.getBearing()
    component.lon = map.getCenter().lng
    component.lat = map.getCenter().lat
    component.pitch = map.getPitch()
    component.ignoreCameraChanges = false
  });

  component.map = map

  component.markers.forEach(m => {
    const marker = new maplibregl.Marker()
      .setLngLat([m.lon, m.lat])
    if (m.html) marker.setPopup(new maplibregl.Popup().setHTML(m.html))
    marker.addTo(map)
  })

  if (component.navigationcontrol) {
    map.addControl(new maplibregl.NavigationControl({
      visualizePitch: true,
      showZoom: true,
      showCompass: true
    }))
  }

  if (component.inspect) {
    map.addControl(new MaplibreInspect({
      popup: new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false
      })
    }));
  }

  component.dispatchEvent(new CustomEvent('map', { detail: { map } }))
}
export default maplib
