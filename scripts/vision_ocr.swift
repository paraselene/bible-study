import Foundation
import Vision
import AppKit

// Native accurate OCR; coordinates are normalized, with the origin at top left.
for path in CommandLine.arguments.dropFirst() {
    guard let image = NSImage(contentsOfFile: path),
          let data = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: data),
          let cgImage = bitmap.cgImage else { fatalError("Cannot read \(path)") }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["en-US"]
    request.usesLanguageCorrection = true
    request.usesCPUOnly = true
    let handler = VNImageRequestHandler(cgImage: cgImage)
    try handler.perform([request])
    let lines: [[String: Any]] = (request.results ?? []).compactMap { observation in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let box = observation.boundingBox
        return ["text": candidate.string, "confidence": candidate.confidence,
                "bbox": [box.minX, 1-box.maxY, box.maxX, 1-box.minY]]
    }
    let output = try JSONSerialization.data(withJSONObject: lines, options: [.prettyPrinted, .sortedKeys])
    try output.write(to: URL(fileURLWithPath: path).deletingPathExtension().appendingPathExtension("vision.json"))
    print("\(path): \(lines.count) lines")
}
