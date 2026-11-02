import Photos
import SwiftUI

private enum GalleryMode: String, CaseIterable, Identifiable {
    case groups = "Similar Groups"
    case roll = "Continuous Roll"
    case find = "Find Similar"
    var id: String { rawValue }
}

struct ContentView: View {
    @EnvironmentObject private var library: PhotoLibraryStore
    @State private var mode: GalleryMode = .groups
    @State private var threshold: Double = 9.0

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 5), count: 3)

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    intro
                    if library.canRead {
                        scanControls
                        if !library.items.isEmpty {
                            Picker("View", selection: $mode) {
                                ForEach(GalleryMode.allCases) { mode in
                                    Text(mode.rawValue).tag(mode)
                                }
                            }
                            .pickerStyle(.menu)
                            .tint(.primary)

                            switch mode {
                            case .groups: groupGallery
                            case .roll: photoGrid(SimilarityEngine.continuousRoll(library.items))
                            case .find: findGallery
                            }
                        }
                    } else {
                        accessRequest
                    }
                }
                .padding()
            }
            .navigationTitle("Similarity Camera Roll")
            .navigationBarTitleDisplayMode(.inline)
            .task { library.refreshLibrary() }
        }
    }

    private var intro: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Your photos, visually connected.")
                .font(.title2.bold())
            Text("Scan your photo library on-device, then explore Similar Groups, Continuous Roll, and Find Similar. Original photos stay untouched.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }

    private var accessRequest: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Photo access required")
                .font(.headline)
            Text("Full access lets the app scan your library. Limited access scans only the photos you choose.")
                .font(.subheadline)
            Button("Allow Photos Access") { Task { await library.requestAccess() } }
                .buttonStyle(.borderedProminent)
            if library.permission == .denied || library.permission == .restricted {
                Text("Photos access is unavailable. Enable access in iPhone Settings → Privacy & Security → Photos.")
                    .font(.caption)
            }
        }
    }

    private var scanControls: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("\(library.items.count) indexed · \(library.totalAvailable) accessible")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            if library.permission == .limited {
                Text("Limited Photos access: only selected assets are visible.")
                    .font(.caption)
                    .foregroundStyle(.orange)
            }
            if library.scanning {
                ProgressView("Analyzing \(library.processed) items…")
            }
            HStack {
                Button("Scan next 100") { library.scanNext() }
                    .buttonStyle(.borderedProminent)
                    .disabled(!library.canScanMore)
                Button("Reset") { library.resetIndex() }
                    .buttonStyle(.bordered)
                    .disabled(library.scanning)
            }
            if let message = library.message {
                Text(message).font(.caption).foregroundStyle(.secondary)
            }
            if library.processed >= 600 {
                Text("Prototype limit reached (600 items). Scalable persistent indexing is planned next.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var groupGallery: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("Group distance").font(.caption)
                Slider(value: $threshold, in: 3...18, step: 1)
                Text("\(Int(threshold))").font(.caption.monospacedDigit())
            }
            Text("Smaller distance means stricter grouping.").font(.caption).foregroundStyle(.secondary)
            let groups = SimilarityEngine.groups(library.items, maxDistance: Float(threshold))
            ForEach(groups.indices, id: \.self) { index in
                VStack(alignment: .leading, spacing: 8) {
                    Text("Group \(index + 1) · \(groups[index].count) items")
                        .font(.headline)
                    photoGrid(groups[index])
                }
            }
        }
    }

    private var findGallery: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Tap any thumbnail in either gallery to find its closest matches.")
                .font(.subheadline).foregroundStyle(.secondary)
            if let selected = library.items.first(where: { $0.id == library.selectedID }) {
                Text("Matches for selected photo").font(.headline)
                photoGrid([selected])
                Text("Closest matches").font(.headline)
                photoGrid(SimilarityEngine.neighbors(of: selected, in: library.items))
            } else {
                photoGrid(library.items)
            }
        }
    }

    private func photoGrid(_ items: [IndexedAsset]) -> some View {
        LazyVGrid(columns: columns, spacing: 5) {
            ForEach(items) { item in
                Button {
                    library.selectedID = item.id
                    mode = .find
                } label: {
                    AssetThumbnail(asset: item.asset)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Find photos like this image")
            }
        }
    }
}
