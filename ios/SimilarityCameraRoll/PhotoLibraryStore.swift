import Foundation
import Photos
import Vision
import UIKit

struct IndexedAsset: Identifiable {
    let id: String
    let asset: PHAsset
    let feature: VNFeaturePrintObservation
}

@MainActor
final class PhotoLibraryStore: ObservableObject {
    @Published var permission: PHAuthorizationStatus = PHPhotoLibrary.authorizationStatus(for: .readWrite)
    @Published var items: [IndexedAsset] = []
    @Published var scanning = false
    @Published var processed = 0
    @Published var skipped = 0
    @Published var totalAvailable = 0
    @Published var message: String?
    @Published var selectedID: String?

    private let batchSize = 100
    private let scanCap = 600
    private var nextOffset = 0
    private var scanTask: Task<Void, Never>?

    var canRead: Bool { permission == .authorized || permission == .limited }
    var canScanMore: Bool { canRead && !scanning && nextOffset < min(totalAvailable, scanCap) }

    func requestAccess() async {
        let status = await PHPhotoLibrary.requestAuthorization(for: .readWrite)
        permission = status
        refreshLibrary()
    }

    func refreshLibrary() {
        permission = PHPhotoLibrary.authorizationStatus(for: .readWrite)
        guard canRead else {
            totalAvailable = 0
            items = []
            return
        }
        totalAvailable = Self.fetchAssets().count
    }

    func resetIndex() {
        guard !scanning else { return }
        items = []
        processed = 0
        skipped = 0
        nextOffset = 0
        selectedID = nil
        message = nil
        refreshLibrary()
    }

    func scanNext() {
        guard canScanMore else { return }
        let assets = Self.fetchAssets()
        let end = min(nextOffset + batchSize, assets.count, scanCap)
        guard nextOffset < end else { return }
        let range = nextOffset..<end
        nextOffset = end
        scanning = true
        message = nil

        scanTask = Task { [weak self] in
            guard let self else { return }
            for index in range {
                if Task.isCancelled { break }
                let asset = assets.object(at: index)
                // PhotoKit's synchronous request avoids races around the image callback.
                let observation = await Task.detached(priority: .utility) {
                    Self.featurePrint(for: asset)
                }.value
                if let observation {
                    self.items.append(IndexedAsset(id: asset.localIdentifier, asset: asset, feature: observation))
                } else {
                    self.skipped += 1
                }
                self.processed += 1
            }
            self.scanning = false
            if self.skipped > 0 {
                self.message = "\(self.skipped) item(s) could not be analyzed, possibly due to iCloud access."
            }
            self.scanTask = nil
        }
    }

    nonisolated private static func fetchAssets() -> PHFetchResult<PHAsset> {
        let options = PHFetchOptions()
        options.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
        options.includeHiddenAssets = false
        return PHAsset.fetchAssets(with: options)
    }

    nonisolated private static func featurePrint(for asset: PHAsset) -> VNFeaturePrintObservation? {
        let options = PHImageRequestOptions()
        options.isSynchronous = true
        options.deliveryMode = .highQualityFormat
        options.resizeMode = .exact
        options.isNetworkAccessAllowed = true
        var fetchedImage: UIImage?
        PHImageManager.default().requestImage(
            for: asset,
            targetSize: CGSize(width: 512, height: 512),
            contentMode: .aspectFit,
            options: options
        ) { image, _ in
            fetchedImage = image
        }
        guard let cgImage = fetchedImage?.cgImage else { return nil }
        let request = VNGenerateImageFeaturePrintRequest()
        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        do {
            try handler.perform([request])
            return request.results?.first as? VNFeaturePrintObservation
        } catch {
            return nil
        }
    }
}
