.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>

.. |nbsp| unicode:: 0xA0
   :trim:

==================
yarn README
==================

Yarn is an alternative to npm that is becoming more widely used though there is
still intense npm v. yarn debate.

It's used for the internetarchive role partly because its faster and with MUCH
less confusing error messages, partly because it does a better job of
deduplicating nested modules - reducing disk and bandwidth usage but more
importantly because the resulting node_modules is deterministic, so we can
reach down and link to inner modules (dweb-archive and dweb-transports in
particular) with certainty about where they will be.
