import Photos
import SwiftUI

struct AssetThumbnail: View {
    let asset: PHAsset
    @State private var image: UIImage?

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Rectangle().fill(.gray.opacity(0.12))
                if let image {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                        .frame(width: geometry.size.width, height: geometry.size.height)
                        .clipped()
                } else {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
                if asset.mediaType == .video {
                    Image(systemName: "video.fill")
                        .foregroundStyle(.white)
                        .shadow(radius: 3)
                        .padding(6)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)
                }
            }
        }
        .aspectRatio(1, contentMode: .fit)
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .task(id: asset.localIdentifier) {
            let options = PHImageRequestOptions()
            options.deliveryMode = .opportunistic
            options.resizeMode = .fast
            options.isNetworkAccessAllowed = true
            PHImageManager.default().requestImage(
                for: asset,
                targetSize: CGSize(width: 300, height: 300),
                contentMode: .aspectFill,
                options: options
            ) { result, _ in
                guard let result else { return }
                Task { @MainActor in self.image = result }
            }
        }
    }
}
