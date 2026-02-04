#ifndef FACE_TRACKER_H
#define FACE_TRACKER_H

// Use specific OpenCV headers to avoid macOS 'NO' macro conflict
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/objdetect.hpp>

// Forward declare OBS types to avoid heavy include
struct obs_source;
typedef struct obs_source obs_source_t;
#include <vector>
#include <atomic>
#include <mutex>

// Face detection data structure
struct FaceData {
    float center_x;
    float center_y;
    float width;
    float height;
    float rotation;
    float confidence;
    std::vector<cv::Point2f> landmarks;
};

class FaceTracker {
public:
    FaceTracker();
    ~FaceTracker();
    
    bool initialize();
    void shutdown();
    
    // Process a frame and return face detection data
    FaceData process_frame(obs_source_t *source);
    
    // Process OpenCV Mat directly
    FaceData process_mat(const cv::Mat &frame);
    
    // Configuration
    void set_detection_confidence(float confidence);
    void set_tracking_mode(bool enabled);
    
    // Status
    bool is_initialized() const { return initialized; }
    
private:
    cv::CascadeClassifier face_cascade;
    cv::CascadeClassifier eye_cascade;
    
    std::atomic<bool> initialized;
    std::atomic<bool> tracking_mode;
    std::atomic<float> detection_confidence;
    
    std::mutex tracker_mutex;
    
    // Previous face data for tracking
    FaceData previous_face;
    std::atomic<bool> has_previous;
    
    // Smoothing
    float smooth_factor;
    
    // Helper methods
    bool load_cascades();
    FaceData detect_faces(const cv::Mat &gray);
    FaceData track_face(const cv::Mat &gray, const FaceData &previous);
    std::vector<cv::Point2f> detect_landmarks(const cv::Mat &face_roi);
    float calculate_rotation(const std::vector<cv::Point2f> &landmarks);
};

#endif // FACE_TRACKER_H
