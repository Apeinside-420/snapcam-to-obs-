#include "face-tracker.h"
#include <obs-module.h>
#include <graphics/graphics.h>

FaceTracker::FaceTracker()
    : initialized(false)
    , tracking_mode(true)
    , detection_confidence(0.5f)
    , has_previous(false)
    , smooth_factor(0.3f)
{
    previous_face = {0.5f, 0.5f, 0.0f, 0.0f, 0.0f, 0.0f, {}};
}

FaceTracker::~FaceTracker()
{
    shutdown();
}

bool FaceTracker::initialize()
{
    std::lock_guard<std::mutex> lock(tracker_mutex);
    
    if (initialized) {
        return true;
    }
    
    if (!load_cascades()) {
        blog(LOG_ERROR, "Failed to load face detection cascades");
        return false;
    }
    
    initialized = true;
    blog(LOG_INFO, "Face tracker initialized successfully");
    return true;
}

void FaceTracker::shutdown()
{
    std::lock_guard<std::mutex> lock(tracker_mutex);
    initialized = false;
}

bool FaceTracker::load_cascades()
{
    // Try multiple paths for the cascade files
    std::vector<std::string> possible_paths = {
        // macOS Homebrew (Apple Silicon)
        "/opt/homebrew/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/opt/homebrew/opt/opencv/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        // macOS Homebrew (Intel)
        "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/local/opt/opencv/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        // Linux
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
    };

    // Add module path if available (may return NULL)
    char *module_cascade = obs_module_file("data/haarcascade_frontalface_default.xml");
    if (module_cascade) {
        possible_paths.insert(possible_paths.begin(), module_cascade);
        bfree(module_cascade);
    }

    for (const auto &path : possible_paths) {
        if (face_cascade.load(path)) {
            blog(LOG_INFO, "Loaded face cascade from: %s", path.c_str());
            break;
        }
    }

    if (face_cascade.empty()) {
        blog(LOG_ERROR, "Could not load face detection cascade");
        return false;
    }

    // Try to load eye cascade for better tracking
    std::vector<std::string> eye_paths = {
        // macOS Homebrew (Apple Silicon)
        "/opt/homebrew/share/opencv4/haarcascades/haarcascade_eye.xml",
        "/opt/homebrew/opt/opencv/share/opencv4/haarcascades/haarcascade_eye.xml",
        // macOS Homebrew (Intel)
        "/usr/local/share/opencv4/haarcascades/haarcascade_eye.xml",
        "/usr/local/opt/opencv/share/opencv4/haarcascades/haarcascade_eye.xml",
        // Linux
        "/usr/share/opencv4/haarcascades/haarcascade_eye.xml",
        "/usr/share/opencv/haarcascades/haarcascade_eye.xml",
    };

    // Add module path if available (may return NULL)
    char *module_eye = obs_module_file("data/haarcascade_eye.xml");
    if (module_eye) {
        eye_paths.insert(eye_paths.begin(), module_eye);
        bfree(module_eye);
    }

    for (const auto &path : eye_paths) {
        if (eye_cascade.load(path)) {
            blog(LOG_INFO, "Loaded eye cascade from: %s", path.c_str());
            break;
        }
    }

    return true;
}

FaceData FaceTracker::process_frame(obs_source_t *source)
{
    if (!initialized || !source) {
        return {0.5f, 0.5f, 0.0f, 0.0f, 0.0f, 0.0f, {}};
    }
    
    // Get frame from OBS source
    // This is a simplified version - in production you'd use proper OBS texture handling
    
    // For now, return default/tracking data
    std::lock_guard<std::mutex> lock(tracker_mutex);
    
    if (has_previous && tracking_mode) {
        return previous_face;
    }
    
    return {0.5f, 0.5f, 0.0f, 0.0f, 0.0f, 0.0f, {}};
}

FaceData FaceTracker::process_mat(const cv::Mat &frame)
{
    if (!initialized || frame.empty()) {
        return {0.5f, 0.5f, 0.0f, 0.0f, 0.0f, 0.0f, {}};
    }
    
    std::lock_guard<std::mutex> lock(tracker_mutex);
    
    // Convert to grayscale
    cv::Mat gray;
    if (frame.channels() == 3) {
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
    } else if (frame.channels() == 4) {
        cv::cvtColor(frame, gray, cv::COLOR_BGRA2GRAY);
    } else {
        gray = frame;
    }
    
    // Equalize histogram for better detection
    cv::Mat equalized;
    cv::equalizeHist(gray, equalized);
    
    FaceData current_face;
    
    if (has_previous && tracking_mode) {
        // Use tracking for smoother results
        current_face = track_face(equalized, previous_face);
    } else {
        // Full detection
        current_face = detect_faces(equalized);
    }
    
    // Smooth the results
    if (has_previous) {
        current_face.center_x = previous_face.center_x * (1.0f - smooth_factor) + 
                                current_face.center_x * smooth_factor;
        current_face.center_y = previous_face.center_y * (1.0f - smooth_factor) + 
                                current_face.center_y * smooth_factor;
        current_face.width = previous_face.width * (1.0f - smooth_factor) + 
                            current_face.width * smooth_factor;
        current_face.height = previous_face.height * (1.0f - smooth_factor) + 
                             current_face.height * smooth_factor;
        current_face.rotation = previous_face.rotation * (1.0f - smooth_factor) + 
                             current_face.rotation * smooth_factor;
    }
    
    previous_face = current_face;
    has_previous = current_face.confidence > detection_confidence;
    
    return current_face;
}

FaceData FaceTracker::detect_faces(const cv::Mat &gray)
{
    std::vector<cv::Rect> faces;
    
    // Detect faces
    face_cascade.detectMultiScale(gray, faces, 1.1, 3, 0, cv::Size(80, 80));
    
    FaceData result = {0.5f, 0.5f, 0.0f, 0.0f, 0.0f, 0.0f, {}};
    
    if (faces.empty()) {
        return result;
    }
    
    // Use the largest face
    cv::Rect main_face = faces[0];
    for (const auto &face : faces) {
        if (face.area() > main_face.area()) {
            main_face = face;
        }
    }
    
    // Calculate normalized coordinates
    float img_width = static_cast<float>(gray.cols);
    float img_height = static_cast<float>(gray.rows);
    
    result.center_x = (main_face.x + main_face.width / 2.0f) / img_width;
    result.center_y = (main_face.y + main_face.height / 2.0f) / img_height;
    result.width = main_face.width / img_width;
    result.height = main_face.height / img_height;
    result.confidence = 0.8f;
    
    // Extract face ROI for landmarks
    cv::Mat face_roi = gray(main_face);
    result.landmarks = detect_landmarks(face_roi);
    
    // Adjust landmark coordinates to full image space
    for (auto &lm : result.landmarks) {
        lm.x += main_face.x;
        lm.y += main_face.y;
        lm.x /= img_width;
        lm.y /= img_height;
    }
    
    // Calculate rotation from landmarks
    if (result.landmarks.size() >= 2) {
        result.rotation = calculate_rotation(result.landmarks);
    }
    
    return result;
}

FaceData FaceTracker::track_face(const cv::Mat &gray, const FaceData &previous)
{
    // Simple tracking: search in region around previous face
    int img_w = gray.cols;
    int img_h = gray.rows;
    
    int prev_x = static_cast<int>(previous.center_x * img_w - previous.width * img_w / 2);
    int prev_y = static_cast<int>(previous.center_y * img_h - previous.height * img_h / 2);
    int prev_w = static_cast<int>(previous.width * img_w);
    int prev_h = static_cast<int>(previous.height * img_h);
    
    // Expand search region
    int search_margin = static_cast<int>(prev_w * 0.5);
    int search_x = std::max(0, prev_x - search_margin);
    int search_y = std::max(0, prev_y - search_margin);
    int search_w = std::min(img_w - search_x, prev_w + 2 * search_margin);
    int search_h = std::min(img_h - search_y, prev_h + 2 * search_margin);
    
    if (search_w <= 0 || search_h <= 0) {
        return detect_faces(gray);
    }
    
    cv::Rect search_region(search_x, search_y, search_w, search_h);
    cv::Mat search_area = gray(search_region);
    
    std::vector<cv::Rect> faces;
    face_cascade.detectMultiScale(search_area, faces, 1.1, 3, 0, 
                                  cv::Size(prev_w / 2, prev_h / 2),
                                  cv::Size(prev_w * 2, prev_h * 2));
    
    if (faces.empty()) {
        // Fall back to full detection if tracking fails
        return detect_faces(gray);
    }
    
    // Find face closest to previous position
    cv::Rect best_face = faces[0];
    float best_distance = std::numeric_limits<float>::max();
    
    for (const auto &face : faces) {
        float face_center_x = search_x + face.x + face.width / 2.0f;
        float face_center_y = search_y + face.y + face.height / 2.0f;
        
        float prev_center_x = previous.center_x * img_w;
        float prev_center_y = previous.center_y * img_h;
        
        float dist = std::sqrt(std::pow(face_center_x - prev_center_x, 2) + 
                               std::pow(face_center_y - prev_center_y, 2));
        
        if (dist < best_distance) {
            best_distance = dist;
            best_face = face;
        }
    }
    
    FaceData result;
    result.center_x = (search_x + best_face.x + best_face.width / 2.0f) / img_w;
    result.center_y = (search_y + best_face.y + best_face.height / 2.0f) / img_h;
    result.width = best_face.width / img_w;
    result.height = best_face.height / img_h;
    result.confidence = 0.85f; // Higher confidence when tracking
    
    // Get landmarks
    cv::Mat face_roi = gray(cv::Rect(search_x + best_face.x, 
                                      search_y + best_face.y,
                                      best_face.width, best_face.height));
    result.landmarks = detect_landmarks(face_roi);
    
    for (auto &lm : result.landmarks) {
        lm.x += search_x + best_face.x;
        lm.y += search_y + best_face.y;
        lm.x /= img_w;
        lm.y /= img_h;
    }
    
    if (result.landmarks.size() >= 2) {
        result.rotation = calculate_rotation(result.landmarks);
    }
    
    return result;
}

std::vector<cv::Point2f> FaceTracker::detect_landmarks(const cv::Mat &face_roi)
{
    std::vector<cv::Point2f> landmarks;
    
    // Simple landmark detection using eye cascade
    if (!eye_cascade.empty()) {
        std::vector<cv::Rect> eyes;
        eye_cascade.detectMultiScale(face_roi, eyes, 1.1, 3, 0, cv::Size(20, 20));
        
        for (const auto &eye : eyes) {
            landmarks.emplace_back(eye.x + eye.width / 2.0f, 
                                 eye.y + eye.height / 2.0f);
        }
    }
    
    return landmarks;
}

float FaceTracker::calculate_rotation(const std::vector<cv::Point2f> &landmarks)
{
    if (landmarks.size() < 2) {
        return 0.0f;
    }
    
    // Calculate rotation based on eye positions
    // Assuming first two landmarks are eyes
    const cv::Point2f &left_eye = landmarks[0];
    const cv::Point2f &right_eye = landmarks[1];
    
    float dx = right_eye.x - left_eye.x;
    float dy = right_eye.y - left_eye.y;
    
    return std::atan2(dy, dx);
}

void FaceTracker::set_detection_confidence(float confidence)
{
    detection_confidence = std::max(0.0f, std::min(1.0f, confidence));
}

void FaceTracker::set_tracking_mode(bool enabled)
{
    tracking_mode = enabled;
}
