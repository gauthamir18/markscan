import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'extraction_screen.dart';

class CameraScreen extends StatefulWidget {
  final String selectedClass;
  final String testCode;

  const CameraScreen({
    super.key,
    required this.selectedClass,
    required this.testCode,
  });

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? controller;
  List<CameraDescription> cameras = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    initializeCamera();
  }

  Future<void> initializeCamera() async {
    try {
      cameras = await availableCameras();

      if (cameras.isEmpty) {
        setState(() {
          isLoading = false;
        });
        return;
      }

      controller = CameraController(
        cameras.first,
        ResolutionPreset.high,
        enableAudio: false,
      );

      await controller!.initialize();

      if (!mounted) return;

      setState(() {
        isLoading = false;
      });
    } catch (e) {
      debugPrint('Camera initialization error: $e');

      if (!mounted) return;

      setState(() {
        isLoading = false;
      });
    }
  }

  Future<void> captureImage() async {
    if (controller == null || !controller!.value.isInitialized) {
      return;
    }

    try {
      final image = await controller!.takePicture();

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ExtractionScreen(
            imagePath: image.path,
            selectedClass: widget.selectedClass,
            testCode: widget.testCode,
          ),
        ),
      );
    } catch (e) {
      debugPrint('Capture error: $e');

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Unable to capture image. Please try again.',
          ),
        ),
      );
    }
  }

  @override
  void dispose() {
    controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const darkBlue = Color(0xFF0D2B45);

    return Scaffold(
      backgroundColor: Colors.black,

      appBar: AppBar(
        backgroundColor: darkBlue,
        foregroundColor: Colors.white,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Scan Seal',
              style: TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              '${widget.selectedClass} • ${widget.testCode}',
              style: const TextStyle(
                fontSize: 12,
                color: Colors.white70,
              ),
            ),
          ],
        ),
      ),

      body: Stack(
        children: [
          if (isLoading)
            const Center(
              child: CircularProgressIndicator(
                color: Colors.white,
              ),
            )
          else if (controller == null ||
              !controller!.value.isInitialized)
            const Center(
              child: Text(
                'Camera unavailable',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                ),
              ),
            )
          else
            Positioned.fill(
              child: CameraPreview(controller!),
            ),

          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Container(
              padding: const EdgeInsets.fromLTRB(
                24,
                18,
                24,
                30,
              ),
              color: Colors.black.withValues(alpha: 0.65),
              child: Column(
                children: [
                  const Text(
                    'Place the seal inside the camera view',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                  ),

                  const SizedBox(height: 18),

                  GestureDetector(
                    onTap: captureImage,
                    child: Container(
                      width: 76,
                      height: 76,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white,
                        border: Border.all(
                          color: Colors.white54,
                          width: 5,
                        ),
                      ),
                      child: const Icon(
                        Icons.camera_alt,
                        color: darkBlue,
                        size: 32,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}