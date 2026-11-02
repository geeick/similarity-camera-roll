import SwiftUI

@main
struct SimilarityCameraRollApp: App {
    @StateObject private var library = PhotoLibraryStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(library)
        }
    }
}
