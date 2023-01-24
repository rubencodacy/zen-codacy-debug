zend v3.2.0
=========

## Breaking changes
* change parameters order in Python test helper function `assert_equal()` https://github.com/HorizenOfficial/zen/commit/d94b92dceedee18897ea54296cc35cfa1d1ccdad

## New Features and Improvements
* Backport `z_mergetoaddress()` and `z_listunspent()` RPC from Zcash https://github.com/HorizenOfficial/zen/pull/446. 
* `z_sendmany()`: allow outputs to the same recipient multiple times https://github.com/HorizenOfficial/zen/pull/447
* Python test logs improved https://github.com/HorizenOfficial/zen/pull/464
* Build system https://github.com/HorizenOfficial/zen/pull/431
    * Added a new configure argument to enable the -Wall flag during the compilation
    * Added the `--use-clang` argument to `build.sh` to switch the compilation from gcc to clang
    * Added some scripts to perform static code analysis with cppcheck and oclint
    * Added support for C++ 17 compilation

## Bugfixes and Minor Changes
* Fix miner thread shutdown https://github.com/HorizenOfficial/zen/pull/459
* Fix IsInitialBlockDownload false positive error message https://github.com/HorizenOfficial/zen/pull/453
* `z_sendmany()`: Fix long-lasting bug with unspendable shielded notes due to a race condition with witness cache flush to disk https://github.com/HorizenOfficial/zen/pull/448
* Fixes https://github.com/zcash/zcash/issues/2793 . Backport commit f33afd3 to increase dbcache default.
* Build system:  Updated to be compatible with latest Linux distributions https://github.com/HorizenOfficial/zen/pull/452

## Security
[section placeholder]

## Known bugs
[section placeholder]

## Contributors
Thanks to Alessandro Petrini, Daniele Rogora and Todd VanGundy for their first contribution to zend!

Alessandro Petrini, Brad Miller, Daniele Rogora, Jack Grigg, Jonathan "Duke" Leto, Paolo Tagliaferri, Simon Liu, Todd VanGundy, cronicc



