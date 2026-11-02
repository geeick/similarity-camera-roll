import Foundation
import Vision

enum SimilarityEngine {
    static func distance(_ a: VNFeaturePrintObservation, _ b: VNFeaturePrintObservation) -> Float {
        var result: Float = .greatestFiniteMagnitude
        do {
            try a.computeDistance(&result, to: b)
            return result
        } catch {
            return .greatestFiniteMagnitude
        }
    }

    static func neighbors(of selected: IndexedAsset, in items: [IndexedAsset], limit: Int = 30) -> [IndexedAsset] {
        items.filter { $0.id != selected.id }
            .map { ($0, distance(selected.feature, $0.feature)) }
            .sorted { $0.1 < $1.1 }
            .prefix(limit)
            .map(\.0)
    }

    static func groups(_ items: [IndexedAsset], maxDistance: Float = 9.0) -> [[IndexedAsset]] {
        // Greedy exemplar groups, using the first image in each group as its representative.
        var result: [[IndexedAsset]] = []
        for item in items {
            var closest: Int?
            var closestDistance = maxDistance
            for i in result.indices {
                guard let first = result[i].first else { continue }
                let d = distance(item.feature, first.feature)
                if d < closestDistance {
                    closestDistance = d
                    closest = i
                }
            }
            if let i = closest {
                result[i].append(item)
            } else {
                result.append([item])
            }
        }
        return result.sorted { $0.count > $1.count }
    }

    static func continuousRoll(_ items: [IndexedAsset]) -> [IndexedAsset] {
        guard let start = items.first else { return [] }
        var remaining = Array(items.dropFirst())
        var sorted = [start]
        while !remaining.isEmpty {
            let current = sorted[sorted.count - 1]
            var bestIndex = 0
            var bestDistance = Float.greatestFiniteMagnitude
            for i in remaining.indices {
                let d = distance(current.feature, remaining[i].feature)
                if d < bestDistance {
                    bestDistance = d
                    bestIndex = i
                }
            }
            sorted.append(remaining.remove(at: bestIndex))
        }
        return sorted
    }
}
