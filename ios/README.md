# Native iPhone app (SwiftUI + PhotoKit + Vision)

This is the first **on-device iPhone prototype** for Similarity Camera Roll. It does not require a Mac-hosted server, Python, Streamlit, or access to your exported photo folders.

## Install on your iPhone

You need a Mac, Xcode, an Apple ID for personal signing, and an iPhone running iOS 17 or newer.

1. Install [Xcode](https://developer.apple.com/xcode/) from Apple.
2. Open **Terminal** on your Mac and run:

   ```bash
   git clone https://github.com/geeick/similarity-camera-roll.git
   cd similarity-camera-roll/ios
   brew install xcodegen
   xcodegen generate
   open SimilarityCameraRoll.xcodeproj
   ```

   If you already cloned this repository, run `git pull` rather than cloning again. If Homebrew is missing, install it using [Homebrew's official instructions](https://brew.sh/), or install XcodeGen using an alternative method listed on [XcodeGen GitHub](https://github.com/yonaskolb/XcodeGen).

3. In Xcode, select the **SimilarityCameraRoll** project and the **SimilarityCameraRoll** app target. Open **Signing & Capabilities**, enable **Automatically manage signing**, and select your **Team** (your Apple ID / Personal Team). Change the Bundle Identifier if Xcode says it is taken.
4. Connect and unlock your iPhone, trust the computer, and enable **Developer Mode** on the phone if requested.
5. Choose your iPhone as the run destination near the top of Xcode and click **Run ▶︎**.
6. On the iPhone, grant Photos access. Select **Full Access** if you intend to analyze the whole accessible library. **Limited Access** is also supported and indexes only the selected images.
7. Tap **Scan next 100**, then choose **Similar Groups**, **Continuous Roll**, or **Find Similar**. Tap any image in any view to jump to its nearest neighbors.

## Current features

- Native SwiftUI photo gallery.
- Reads authorized images and videos from your iPhone Photos library through PhotoKit.
- Compares images with Apple's Vision feature-print API, independent of filename, dates, and metadata.
- Video assets are currently represented by poster images only (not frame-by-frame matching).
- Similar Groups, Continuous Roll, and Find Similar.
- Incremental batches of 100 items with a **600-item safety cap for the prototype**.
- Photos and videos are never changed, deleted, duplicated, or uploaded by this app.

## Known limitations

- **This is not yet a full-camera-roll indexer.** The prototype limits itself to 600 accessible items per app session to avoid long-running scans, heat, and memory pressure. A persistent, scalable index is the next engineering task.
- The index is in memory and is recreated if the app is closed. Scanning large libraries repeatedly is inefficient.
- Group similarity uses a default Vision feature-print distance threshold; it may not recognize different photos of the same subject.
- A screenshot with a tiny embedded photo and a video sent by different people may not match yet. We'll add region-based matching and multi-frame video fingerprints later.
- iCloud-only assets may need to download to the device while scanning. If they cannot be retrieved, the app skips them and counts a failure.
- This is a starter project, not a compiled or App-Store-distributed app. Native compilation and on-device testing must be performed in Xcode on a Mac.

## Implementation notes

- `PhotoLibraryStore.swift`: Photos permission flow, background indexing, Vision image feature prints.
- `SimilarityEngine.swift`: nearest-neighbor search, grouping, and continuous similarity ordering.
- `AssetThumbnail.swift`: lazy thumbnails for PhotoKit assets.
- `ContentView.swift`: the three gallery modes and progress UI.
- `project.yml`: the native iOS project specification. [XcodeGen](https://github.com/yonaskolb/XcodeGen) generates the Xcode project.

Full access is not required to use the app, but it is required to see all items in the Photos library. The app never writes to Photos.
