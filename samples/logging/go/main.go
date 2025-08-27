package main

import (
	"fmt"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"log"
	"net/http"
	"os"
	"strings"
	"time"
)

var (
	logger *zap.Logger
	projectID = os.Getenv("GCP_PROJECT_ID")
)

func init() {
	config := zap.NewProductionConfig()
	config.EncoderConfig.TimeKey = "time"
	config.EncoderConfig.LevelKey = "severity"
	config.EncoderConfig.MessageKey = "message"
	config.EncoderConfig.EncodeLevel = zapcore.CapitalLevelEncoder

	// Map zap levels to GCP severity levels
	config.EncoderConfig.EncodeLevel = func(l zapcore.Level, enc zapcore.PrimitiveArrayEncoder) {
		switch l {
		case zapcore.DebugLevel:
			enc.AppendString("DEBUG")
		case zapcore.InfoLevel:
			enc.AppendString("INFO")
		case zapcore.WarnLevel:
			enc.AppendString("WARNING")
		case zapcore.ErrorLevel:
			enc.AppendString("ERROR")
		case zapcore.DPanicLevel:
			enc.AppendString("CRITICAL")
		case zapcore.PanicLevel:
			enc.AppendString("ALERT")
		case zapcore.FatalLevel:
			enc.AppendString("EMERGENCY")
		}
	}

	var err error
	logger, err = config.Build()
	if err != nil {
		panic(err)
	}

	if projectID == "" {
		logger.Warn("GCP_PROJECT_ID environment variable not set. Trace correlation will be affected.")
	}
}

func main() {
	defer logger.Sync()

	http.HandleFunc("/work", handleWork)
	http.HandleFunc("/healthz", handleHealthz)

	logger.Info("Server starting on port 8080",
		zap.String("service", getEnv("K_SERVICE", "sample-logger-go")),
		zap.String("version", getEnv("K_REVISION", "1.0.0")),
	)

	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("http.ListenAndServe: %v", err)
	}
}

func handleWork(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	traceContext := r.Header.Get("x-cloud-trace-context")
	
	fields := getCommonFields(r, traceContext)

	if r.URL.Query().Get("error") == "true" {
		latency := time.Since(start)
		fields = append(fields, zap.Int("status", http.StatusInternalServerError), zap.Float64("latency_ms", float64(latency.Milliseconds())))
		
		logger.Error("Simulated internal server error", fields...)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	latency := time.Since(start)
	fields = append(fields, zap.Int("status", http.StatusOK), zap.Float64("latency_ms", float64(latency.Milliseconds())))
	
	logger.Info("Request processed successfully", fields...)
	fmt.Fprint(w, "Work done successfully")
}

func handleHealthz(w http.ResponseWriter, r *http.Request) {
	logger.Debug("Health check successful", getCommonFields(r, "")...)
	fmt.Fprint(w, "ok")
}

func getCommonFields(r *http.Request, traceContext string) []zap.Field {
	fields := []zap.Field{
		zap.String("service", getEnv("K_SERVICE", "sample-logger-go")),
		zap.String("version", getEnv("K_REVISION", "1.0.0")),
		zap.String("env", getEnv("APP_ENV", "dev")),
		zap.String("tenant", getEnv("TENANT", "default")),
		zap.String("request_id", r.Header.Get("x-request-id")),
		zap.String("http_method", r.Method),
		zap.String("http_path", r.URL.Path),
	}

	if traceContext != "" && projectID != "" {
		parts := strings.Split(traceContext, "/")
		if len(parts) > 0 && len(parts[0]) > 0 {
			traceID := parts[0]
			spanID := ""
			if len(parts) > 1 {
				spanID = strings.Split(parts[1], ";")[0]
			}
			fields = append(fields,
				zap.String("logging.googleapis.com/trace", fmt.Sprintf("projects/%s/traces/%s", projectID, traceID)),
				zap.String("logging.googleapis.com/spanId", spanID),
			)
		}
	}
	return fields
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}
