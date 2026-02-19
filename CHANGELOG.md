# Changelog

## 0.4 - Refactoring, Bugfixes and adding new features

### Features
* **Added method:** Added `Pyghthouse.wait` as a new feature to synchronize with the frame building. Commenly used to ensure building a frame with the previous call of `Pyghthouse.set_image`
* **Added method:** Added `Pyghthouse.keep_running` as a new feature to keep the main thread alive. Useable to let callback functions run until keyboard interrupt
* **Error handeling:** `PyghthouseCanvas.set_image` will now throw more useful errors upon invalid image object

### Changes
* **main thread check:** The pyghthouse routine will now stop when the main thread has died. To keep the pyghthouse routine running, use `Pyghthouse.keep_running`
* **Wait for start:** `Pyghthouse.start` will now wait until the start sequence is completed

### Removed
* **Removed dependency:** numpy has been removed as dependency to simplify the image structure
* **Redundant method:** `Pyghthouse.connect` was only intended for internal use and is now combined in `Pyghthouse.start`
* **Redundant behaviour:** signal handler and corresponding method `Pyghthouse._handle_sigint` is now replaced by the main thread check in `PHThread`
* **Unsupported method:** 
    + removed `Pyghthouse.get_image_raw`
    + removed `Pyghthouse.empty_image_raw`

### Bugfixes
* **Keyboard interrupt:** keyboard interrupt should now stop the whole program instead of only the main thread
* **Missing warning:** `VerbosityLevel.ALL` now prints all messages, instead of only messages with number 200
* **Error handeling:** upon error inside the library, the Pyghthouse routine will now close properly
* **Fixed image mutations:** added locks for critical sections in `PyghthouseCanvas` to prevent rare image mutations.
* **Fixed connection deadlock:** added timeout to avoid deadlocks upon unexpected connection behaviour

### Refactored
* **Added documentation**
* **Changed data structure:** Changed data structure of `PyghthouseCanvas` from a 3D numpy array to a 3D python list
* **Better maintainability:** Changed overall code structure to allow easier access to single code pieces
* **Changed internal package structure:** 
    + moved `PHThread` to the new script `_thread.py`
    + moved `PHMessageHandler` into the new script `handler.py`
    + moved `REID` into the new script `data.py` and renamed from `REID` to `ReID`
    + moved `VerbosityLevel` into the new script `data.py`