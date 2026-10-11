from __future__ import annotations

import html
import os
import zipfile
from datetime import datetime


OUT = "Deepfake_Face_Detector_SRS.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def r(text: str, bold=False, italic=False, color=None, size=None, font=None):
    props = []
    if font:
        props.append(f'<w:rFonts w:ascii="{esc(font)}" w:hAnsi="{esc(font)}"/>')
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{int(size * 2)}"/>')
        props.append(f'<w:szCs w:val="{int(size * 2)}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def fld_simple(instr: str):
    return f'<w:fldSimple w:instr="{esc(instr)}"><w:r><w:t>1</w:t></w:r></w:fldSimple>'


def p(
    text: str = "",
    style: str | None = None,
    runs: list[str] | None = None,
    align: str | None = None,
    before: int | None = None,
    after: int | None = None,
    num_id: int | None = None,
    ilvl: int = 0,
    keep_next: bool = False,
    page_break_before: bool = False,
    border_bottom: str | None = None,
):
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    spacing_attrs = []
    if before is not None:
        spacing_attrs.append(f'w:before="{before}"')
    if after is not None:
        spacing_attrs.append(f'w:after="{after}"')
    if spacing_attrs:
        ppr.append(f"<w:spacing {' '.join(spacing_attrs)}/>")
    if num_id is not None:
        ppr.append(f'<w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="{num_id}"/></w:numPr>')
    if keep_next:
        ppr.append("<w:keepNext/>")
    if page_break_before:
        ppr.append("<w:pageBreakBefore/>")
    if border_bottom:
        ppr.append(
            '<w:pBdr><w:bottom w:val="single" w:sz="10" w:space="6" '
            f'w:color="{border_bottom}"/></w:pBdr>'
        )
    pr = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    body = "".join(runs) if runs is not None else r(text)
    return f"<w:p>{pr}{body}</w:p>"


def h(text: str, level: int):
    return p(text, style=f"Heading{level}", keep_next=True)


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def cell_para(text: str, bold=False, color=None):
    return p(runs=[r(text, bold=bold, color=color, size=9.5)], style="TableText", after=40)


def tc(text, width: int, fill: str | None = None, bold=False, color=None):
    shade = f'<w:shd w:fill="{fill}"/>' if fill else ""
    paras = []
    if isinstance(text, list):
        for item in text:
            paras.append(cell_para(item, bold=bold, color=color))
    else:
        paras.append(cell_para(str(text), bold=bold, color=color))
    return (
        "<w:tc>"
        f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}'
        '<w:vAlign w:val="center"/></w:tcPr>'
        f"{''.join(paras)}"
        "</w:tc>"
    )


def table(rows, widths, header=True, header_fill="F2F4F7"):
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    trs = []
    for row_idx, row in enumerate(rows):
        cells = []
        for idx, value in enumerate(row):
            cells.append(
                tc(
                    value,
                    widths[idx],
                    fill=header_fill if header and row_idx == 0 else None,
                    bold=header and row_idx == 0,
                    color="0B2545" if header and row_idx == 0 else None,
                )
            )
        tr_pr = "<w:trPr><w:tblHeader/></w:trPr>" if header and row_idx == 0 else ""
        trs.append(f"<w:tr>{tr_pr}{''.join(cells)}</w:tr>")
    return (
        "<w:tbl>"
        "<w:tblPr>"
        '<w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblInd w:w="120" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="C9D2DF"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="C9D2DF"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="C9D2DF"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="C9D2DF"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D7DFEA"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="D7DFEA"/>'
        '</w:tblBorders>'
        '<w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>'
        '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tblCellMar>'
        "</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        f"{''.join(trs)}"
        "</w:tbl>"
    )


def callout(title: str, body: str):
    return table(
        [[title], [body]],
        [9360],
        header=True,
        header_fill="E8EEF5",
    )


def doc_xml():
    parts = []
    parts.append(p("SOFTWARE REQUIREMENTS SPECIFICATION", runs=[r("SOFTWARE REQUIREMENTS SPECIFICATION", bold=True, color="0B2545", size=24)], after=80))
    parts.append(p("Deepfake Face Detector", runs=[r("Deepfake Face Detector", bold=True, color="2E74B5", size=18)], after=160))
    parts.append(p("Academic Evaluation Copy", runs=[r("Academic Evaluation Copy", italic=True, color="555555", size=12)], after=220))
    parts.append(table(
        [
            ["Project", "Deepfake Face Detector"],
            ["Prepared for", "Academic evaluation and viva presentation"],
            ["Prepared by", "[Student Name]"],
            ["Version", "1.0"],
            ["Date", "10 October 2026"],
            ["Implementation", "Flask web application with PyTorch EfficientNet-B0 model"],
        ],
        [2200, 7160],
        header=False,
    ))
    parts.append(p("", after=180, border_bottom="2E74B5"))
    parts.append(callout(
        "Document Purpose",
        "This Software Requirements Specification defines the functional, non-functional, interface, data, model, testing, and limitation requirements for the Deepfake Face Detector project. It is written for evaluators, faculty reviewers, and project team members who need a clear view of what the system is intended to do."
    ))
    parts.append(page_break())

    parts.append(h("Document Control", 1))
    parts.append(table(
        [
            ["Field", "Value"],
            ["Document title", "Software Requirements Specification - Deepfake Face Detector"],
            ["Document status", "Evaluation-ready draft"],
            ["System type", "Machine-learning based image classification web application"],
            ["Current model used by application", "model/deepfake_model_v3.pth"],
            ["Primary runtime", "Python 3.11, Flask, PyTorch, Torchvision, OpenCV, PIL"],
        ],
        [2600, 6760],
        header=True,
    ))
    parts.append(h("Revision History", 2))
    parts.append(table(
        [
            ["Version", "Date", "Description", "Author"],
            ["1.0", "10 Oct 2026", "Initial SRS prepared for evaluation submission.", "[Student Name]"],
        ],
        [1100, 1600, 5000, 1660],
        header=True,
    ))
    parts.append(h("Table of Contents", 1))
    toc_items = [
        "1. Introduction",
        "2. Overall Description",
        "3. Functional Requirements",
        "4. External Interface Requirements",
        "5. Non-Functional Requirements",
        "6. Data Requirements",
        "7. System Architecture",
        "8. Machine Learning Model Specification",
        "9. Testing and Acceptance Criteria",
        "10. Risks, Limitations, and Future Enhancements",
        "Appendix A. API Contract",
        "Appendix B. Project Structure",
    ]
    for item in toc_items:
        parts.append(p(item, num_id=1, after=60))
    parts.append(page_break())

    parts.append(h("1. Introduction", 1))
    parts.append(h("1.1 Purpose", 2))
    parts.append(p("The purpose of this SRS is to describe the expected behavior, boundaries, interfaces, and quality requirements of the Deepfake Face Detector system. The document supports implementation review, academic evaluation, and future maintenance."))
    parts.append(h("1.2 Scope", 2))
    parts.append(p("The system is a local web application that accepts a face image from a user, validates that a face is visible, preprocesses the image, runs a trained deep learning classifier, and returns whether the image is predicted as REAL or FAKE with a confidence percentage."))
    parts.append(p("The scope covers single-image detection only. The current system does not perform video analysis, batch processing, identity verification, forensic explanation, or cloud deployment."))
    parts.append(h("1.3 Definitions and Abbreviations", 2))
    parts.append(table(
        [
            ["Term", "Meaning"],
            ["Deepfake", "Synthetic or AI-generated media designed to look realistic."],
            ["SRS", "Software Requirements Specification."],
            ["CNN", "Convolutional Neural Network."],
            ["EfficientNet-B0", "Torchvision image classification backbone used for the two-class model."],
            ["Inference", "The process of using the trained model to predict a class for a new image."],
            ["Confidence", "The highest softmax probability returned by the model, displayed as a percentage."],
        ],
        [2100, 7260],
        header=True,
    ))
    parts.append(h("1.4 References", 2))
    refs = [
        "Project source files: app.py, preprocess.py, dataset.py, train.py, finetune.py, evaluate.py, predict.py.",
        "Dataset used during development: 140k Real and Fake Faces, organized into train, valid, and test folders.",
        "Current application model file: model/deepfake_model_v3.pth.",
        "Python packages used: Flask, PyTorch, Torchvision, OpenCV, Pillow, NumPy, and scikit-learn.",
    ]
    for ref in refs:
        parts.append(p(ref, num_id=2, after=60))

    parts.append(h("2. Overall Description", 1))
    parts.append(h("2.1 Product Perspective", 2))
    parts.append(p("The Deepfake Face Detector is a standalone academic prototype. It combines a browser-based upload interface, a Flask backend, OpenCV-based face detection, and a PyTorch image classification model. The product is intended to demonstrate a complete machine learning workflow from dataset preparation to web-based prediction."))
    parts.append(h("2.2 Product Functions", 2))
    funcs = [
        "Display an upload page for selecting or dragging an image.",
        "Preview the selected image before prediction.",
        "Reject requests with missing, invalid, or non-face images.",
        "Convert the input image to RGB and prepare it for model inference.",
        "Run EfficientNet-B0 model inference using the saved model checkpoint.",
        "Return a REAL or FAKE result with confidence.",
        "Show errors clearly when the model cannot process the input.",
    ]
    for item in funcs:
        parts.append(p(item, num_id=2, after=60))
    parts.append(h("2.3 User Classes", 2))
    parts.append(table(
        [
            ["User Class", "Description", "Primary Goal"],
            ["Student / Developer", "Maintains the project and demonstrates it during evaluation.", "Run the app, explain the model, and test predictions."],
            ["Evaluator / Faculty", "Reviews the project behavior and documentation.", "Understand system design, scope, limitations, and outputs."],
            ["End User", "Uploads a face image through the browser.", "Receive an easy-to-read prediction result."],
        ],
        [1900, 4200, 3260],
        header=True,
    ))
    parts.append(h("2.4 Operating Environment", 2))
    parts.append(table(
        [
            ["Component", "Requirement / Observed Setup"],
            ["Operating system", "Windows development environment."],
            ["Python", "Python 3.11 virtual environment."],
            ["Hardware", "Development setup includes 8 GB RAM and NVIDIA GeForce RTX 2050 GPU as recorded in the progress tracker."],
            ["Browser", "Any modern browser capable of rendering HTML, CSS, and JavaScript."],
            ["Server", "Local Flask development server, typically http://127.0.0.1:5000."],
        ],
        [2200, 7160],
        header=True,
    ))
    parts.append(h("2.5 Constraints", 2))
    constraints = [
        "The classifier is trained for two classes only: fake and real.",
        "The application expects a visible face and rejects images where the Haar cascade detector does not find a face.",
        "The current model is intended for image-level classification and does not provide pixel-level manipulation localization.",
        "The project is currently optimized for local evaluation rather than production deployment.",
        "Dataset characteristics may limit generalization to unseen deepfake generation methods.",
    ]
    for item in constraints:
        parts.append(p(item, num_id=2, after=60))
    parts.append(h("2.6 Assumptions and Dependencies", 2))
    assumptions = [
        "The model file exists at model/deepfake_model_v3.pth before the Flask app starts.",
        "Required libraries are installed inside the project virtual environment.",
        "The uploaded image contains a human face large enough for face detection.",
        "The backend and frontend are served from the same Flask application, so the frontend calls /predict directly.",
    ]
    for item in assumptions:
        parts.append(p(item, num_id=2, after=60))

    parts.append(h("3. Functional Requirements", 1))
    parts.append(p("The following requirements define what the system shall do. Requirement identifiers can be used during evaluation and testing."))
    parts.append(table(
        [
            ["ID", "Requirement", "Priority", "Acceptance Criteria"],
            ["FR-01", "The system shall display a home page with the project title, image upload control, preview area, and prediction button.", "High", "Opening / shows the upload interface without server error."],
            ["FR-02", "The system shall allow the user to select or drag and drop one image file.", "High", "A selected image name is shown and the preview is updated."],
            ["FR-03", "The system shall keep the prediction button disabled until an image is selected.", "Medium", "The button is disabled on first load and becomes enabled after file selection."],
            ["FR-04", "The system shall submit the selected image to the backend /predict endpoint.", "High", "A POST request with multipart form data field file is sent."],
            ["FR-05", "The system shall reject requests without an uploaded file.", "High", "The API returns a clear error with HTTP 400."],
            ["FR-06", "The system shall reject invalid image files.", "High", "The API returns Invalid image file with HTTP 400."],
            ["FR-07", "The system shall detect whether a face is present before model inference.", "High", "Images with no detected face return a clear no-face error."],
            ["FR-08", "The system shall preprocess valid images using resizing, RGB conversion, tensor conversion, and ImageNet normalization.", "High", "The tensor shape and normalization match the transform used during training/inference."],
            ["FR-09", "The system shall classify the image as REAL or FAKE.", "High", "The JSON response contains result equal to REAL or FAKE."],
            ["FR-10", "The system shall display the confidence percentage returned by the model.", "Medium", "The browser result contains the label and numeric confidence."],
            ["FR-11", "The system shall provide evaluation support using test accuracy, confusion matrix, precision, recall, and F1 score.", "Medium", "evaluate.py can be run to print the required metrics on the test set."],
            ["FR-12", "The system shall preserve older model checkpoints when saving updated model versions.", "Medium", "Model files are stored as deepfake_model.pth, deepfake_model_v2.pth, and deepfake_model_v3.pth."],
        ],
        [900, 3900, 1000, 3560],
        header=True,
    ))

    parts.append(h("4. External Interface Requirements", 1))
    parts.append(h("4.1 User Interface", 2))
    parts.append(p("The frontend shall provide a clean upload-first interface. The current UI uses a navy and beige visual style with a 3D scanner-like preview area. It supports image selection, drag-and-drop, preview, loading state, and clear result or error messages."))
    parts.append(h("4.2 Hardware Interface", 2))
    parts.append(p("No special hardware interface is required for end users. For model training and faster inference, a CUDA-capable NVIDIA GPU is beneficial but not mandatory for CPU-based local inference."))
    parts.append(h("4.3 Software Interface", 2))
    parts.append(table(
        [
            ["Software", "Purpose"],
            ["Flask", "Serves the web app and exposes /predict."],
            ["PyTorch", "Loads model weights and performs inference."],
            ["Torchvision", "Provides EfficientNet-B0 architecture and image transforms."],
            ["OpenCV", "Performs Haar cascade face detection."],
            ["Pillow", "Reads uploaded images and converts them to RGB."],
            ["NumPy", "Converts PIL image data for OpenCV processing."],
            ["scikit-learn", "Provides evaluation metrics in evaluate.py."],
        ],
        [2300, 7060],
        header=True,
    ))
    parts.append(h("4.4 Communication Interface", 2))
    parts.append(p("The frontend communicates with the backend using HTTP. The prediction request is a POST request to /predict with multipart/form-data. The response is JSON."))

    parts.append(h("5. Non-Functional Requirements", 1))
    parts.append(table(
        [
            ["ID", "Category", "Requirement"],
            ["NFR-01", "Performance", "For a single image, the system should return a prediction within a few seconds on a typical development laptop after the model has loaded."],
            ["NFR-02", "Reliability", "The application shall load the model once at server startup and use evaluation mode for inference."],
            ["NFR-03", "Usability", "The interface shall be simple enough for a first-time evaluator to upload an image and understand the result without extra instructions."],
            ["NFR-04", "Error Handling", "The system shall show clear messages for missing files, invalid files, no-face images, server errors, and connection errors."],
            ["NFR-05", "Security and Privacy", "Uploaded images shall be processed for prediction only and shall not be intentionally stored by the current application workflow."],
            ["NFR-06", "Maintainability", "Training, preprocessing, evaluation, prediction, backend, and frontend concerns shall remain separated into readable files."],
            ["NFR-07", "Compatibility", "The application shall run in a Python 3.11 virtual environment with the required dependencies installed."],
            ["NFR-08", "Explainability", "The project documentation shall clearly state model scope, dataset limitations, and confidence interpretation."],
        ],
        [900, 1800, 6660],
        header=True,
    ))

    parts.append(h("6. Data Requirements", 1))
    parts.append(h("6.1 Dataset Organization", 2))
    parts.append(p("The primary dataset is organized by split and class folders. The class mapping used by ImageFolder is fake = 0 and real = 1."))
    parts.append(table(
        [
            ["Split", "Fake Images", "Real Images", "Total"],
            ["Train", "50,000", "50,000", "100,000"],
            ["Validation", "10,000", "10,000", "20,000"],
            ["Test", "10,000", "10,000", "20,000"],
            ["Fine-tune train", "5,000", "5,000", "10,000"],
            ["Fine-tune validation", "500", "500", "1,000"],
        ],
        [2200, 2100, 2100, 2960],
        header=True,
    ))
    parts.append(h("6.2 Input Data", 2))
    input_reqs = [
        "Input shall be an image file accepted by the browser and Pillow image loader.",
        "The image should contain one or more visible human faces.",
        "The backend converts the image to RGB before further processing.",
        "For inference, the image is resized and normalized before being passed to the model.",
    ]
    for item in input_reqs:
        parts.append(p(item, num_id=2, after=60))
    parts.append(h("6.3 Output Data", 2))
    parts.append(table(
        [
            ["Field", "Type", "Description"],
            ["result", "String", "Predicted class label: REAL or FAKE."],
            ["confidence", "Number", "Softmax confidence percentage rounded to two decimal places."],
            ["error", "String", "Returned only when the request cannot be processed."],
        ],
        [1700, 1700, 5960],
        header=True,
    ))

    parts.append(h("7. System Architecture", 1))
    parts.append(p("The architecture follows a simple request-response flow suitable for academic evaluation and local demonstration."))
    parts.append(table(
        [
            ["Layer", "Component", "Responsibility"],
            ["Presentation", "templates/index.html, static/style.css, static/script.js", "Image upload, preview, button state, result display, and frontend error handling."],
            ["Application", "app.py", "Flask routes, file validation, face detection, preprocessing call, model inference, JSON response."],
            ["ML preprocessing", "preprocess.py, preprocess_finetune.py", "Resize, augmentation for fine-tuning, tensor conversion, and ImageNet normalization."],
            ["Model", "EfficientNet-B0 checkpoint", "Two-class classification between fake and real."],
            ["Evaluation", "evaluate.py", "Test set evaluation using accuracy, confusion matrix, precision, recall, and F1 score."],
        ],
        [1600, 3000, 4760],
        header=True,
    ))
    parts.append(h("7.1 Request Flow", 2))
    flow_steps = [
        "User selects an image in the browser.",
        "Frontend displays the preview and enables the Check Image button.",
        "Frontend sends the image to POST /predict.",
        "Backend validates the upload and loads it as an RGB image.",
        "OpenCV Haar cascade checks for a visible face.",
        "Image is resized, converted, normalized, and moved to CPU or GPU device.",
        "EfficientNet-B0 predicts class probabilities.",
        "Backend returns JSON result and confidence.",
        "Frontend displays the prediction or a readable error message.",
    ]
    for step in flow_steps:
        parts.append(p(step, num_id=1, after=60))

    parts.append(h("8. Machine Learning Model Specification", 1))
    parts.append(table(
        [
            ["Item", "Specification"],
            ["Architecture", "EfficientNet-B0 from Torchvision."],
            ["Output classes", "2 classes: fake and real."],
            ["Class order", "fake = index 0, real = index 1."],
            ["Loss function", "CrossEntropyLoss."],
            ["Optimizer", "Adam."],
            ["Initial training learning rate", "1e-4."],
            ["Fine-tuning learning rate", "1e-5."],
            ["Batch size", "8 in current dataset loaders."],
            ["Current model file", "model/deepfake_model_v3.pth."],
            ["Inference mode", "model.eval() with torch.no_grad()."],
        ],
        [2500, 6860],
        header=True,
    ))
    parts.append(h("8.1 Training Summary", 2))
    parts.append(p("The initial training run used the full training set for 5 epochs with mixed precision. The progress tracker records validation accuracy above 99 percent during training. The SRS treats these as development training observations, not as a replacement for independent test-set evaluation."))
    parts.append(table(
        [
            ["Epoch", "Loss", "Train Accuracy", "Validation Accuracy"],
            ["1/5", "0.0941", "96.54%", "99.30%"],
            ["2/5", "0.0208", "99.31%", "99.80%"],
            ["3/5", "0.0130", "99.56%", "99.64%"],
            ["4/5", "0.0093", "99.67%", "99.84%"],
            ["5/5", "0.0074", "99.75%", "99.67%"],
        ],
        [1400, 1900, 2800, 3260],
        header=True,
    ))
    parts.append(h("8.2 Preprocessing", 2))
    prep = [
        "Images are resized to 224 x 224 for model input.",
        "Images are converted to tensors.",
        "Images are normalized using ImageNet mean [0.485, 0.456, 0.406] and standard deviation [0.229, 0.224, 0.225].",
        "Fine-tuning augmentation includes random horizontal flip, color jitter, and Gaussian blur.",
        "The Flask endpoint additionally resizes uploaded images to 256 x 256 and applies JPEG compression before the shared transform, matching the intended dataset-like image preparation step.",
    ]
    for item in prep:
        parts.append(p(item, num_id=2, after=60))

    parts.append(h("9. Testing and Acceptance Criteria", 1))
    parts.append(h("9.1 Test Types", 2))
    parts.append(table(
        [
            ["Test Type", "Purpose", "Example"],
            ["Unit / Script Test", "Verify dataset loading, preprocessing, and single-image prediction functions.", "Run dataset.py or predict.py."],
            ["API Test", "Verify /predict behavior for valid and invalid requests.", "Upload valid image, invalid file, no file, and no-face image."],
            ["Model Evaluation", "Measure classification quality on the test set.", "Run evaluate.py and record accuracy, confusion matrix, precision, recall, and F1."],
            ["UI Test", "Verify upload, preview, loading state, and result rendering.", "Open http://127.0.0.1:5000 and test browser workflow."],
            ["Edge Case Test", "Verify graceful handling for problematic inputs.", "Use blurred image, small face, non-image file, and empty request."],
        ],
        [1900, 4050, 3410],
        header=True,
    ))
    parts.append(h("9.2 Acceptance Criteria", 2))
    accept = [
        "The Flask server starts successfully and loads model/deepfake_model_v3.pth.",
        "The home page opens in a browser without layout breakage.",
        "A valid face image returns a JSON prediction and the UI displays it.",
        "Invalid inputs return clear errors instead of crashing the server.",
        "The evaluation script can report accuracy, confusion matrix, precision, recall, and F1 score.",
        "The document and viva explanation clearly state limitations and future improvements.",
    ]
    for item in accept:
        parts.append(p(item, num_id=2, after=60))

    parts.append(h("10. Risks, Limitations, and Future Enhancements", 1))
    parts.append(h("10.1 Risks and Limitations", 2))
    limitations = [
        "The dataset may contain fake images generated using a limited set of generation methods, so performance may be lower on newer or more diverse AI-generated images.",
        "High validation accuracy can be influenced by dataset patterns and should be explained carefully during evaluation.",
        "Haar cascade face detection can fail for side faces, small faces, poor lighting, or occluded faces.",
        "The model predicts only image-level class and does not explain which face region influenced the decision.",
        "The current local Flask server is not production hardened.",
    ]
    for item in limitations:
        parts.append(p(item, num_id=2, after=60))
    parts.append(h("10.2 Future Enhancements", 2))
    future = [
        "Add stronger face detection or face alignment using modern face detectors.",
        "Add threshold tuning based on validation F1 score.",
        "Add Grad-CAM or heatmap visualization to improve explainability.",
        "Support video frame sampling and aggregate prediction.",
        "Add batch image testing for evaluation demonstrations.",
        "Deploy the project to a controlled cloud or academic demo environment.",
        "Store evaluation reports as CSV or PDF for repeatable comparison across model versions.",
    ]
    for item in future:
        parts.append(p(item, num_id=2, after=60))

    parts.append(h("Appendix A. API Contract", 1))
    parts.append(table(
        [
            ["Endpoint", "Method", "Input", "Success Response", "Error Response"],
            ["/", "GET", "None", "HTML frontend page.", "Server error if template/static assets are unavailable."],
            ["/predict", "POST", "multipart/form-data with field file", '{"result": "REAL", "confidence": 98.25}', '{"error": "No file uploaded"} or other validation error.'],
        ],
        [1300, 1100, 2550, 2400, 2010],
        header=True,
    ))
    parts.append(h("Appendix B. Project Structure", 1))
    parts.append(table(
        [
            ["Path / File", "Purpose"],
            ["app.py", "Flask application and prediction endpoint."],
            ["templates/index.html", "Frontend HTML interface."],
            ["static/style.css", "Frontend styling and responsive layout."],
            ["static/script.js", "Frontend upload, preview, fetch, and result handling."],
            ["preprocess.py", "Shared inference transform."],
            ["dataset.py", "Main ImageFolder datasets and DataLoaders."],
            ["train.py", "Initial EfficientNet-B0 training script."],
            ["finetune.py", "Fine-tuning script that saves model/deepfake_model_v3.pth."],
            ["evaluate.py", "Test-set metrics script."],
            ["predict.py", "Standalone single-image prediction script."],
            ["model/", "Saved model checkpoint files."],
            ["dataset/", "Main train/valid/test image dataset."],
            ["dataset_finetune/", "Fine-tuning dataset."],
        ],
        [2800, 6560],
        header=True,
    ))

    body = "".join(parts)
    sect = (
        '<w:sectPr>'
        '<w:headerReference w:type="default" r:id="rId5"/>'
        '<w:footerReference w:type="default" r:id="rId6"/>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="708" w:footer="708" w:gutter="0"/>'
        '<w:cols w:space="720"/>'
        '<w:docGrid w:linePitch="360"/>'
        '</w:sectPr>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:body>{body}{sect}</w:body></w:document>'
    )


def styles_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
  <w:docDefaults>
    <w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:color w:val="111111"/></w:rPr></w:rPrDefault>
    <w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="320" w:after="160"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="2E74B5"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="2E74B5"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="80"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:color w:val="1F4D78"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="40" w:line="250" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Footer"><w:name w:val="Footer"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/><w:color w:val="666666"/></w:rPr></w:style>
</w:styles>'''


def numbering_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{W_NS}">
  <w:abstractNum w:abstractNumId="0">
    <w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="360"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr></w:lvl>
  </w:abstractNum>
  <w:abstractNum w:abstractNumId="1">
    <w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/><w:lvlJc w:val="left"/><w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="360"/></w:pPr><w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/><w:sz w:val="22"/></w:rPr></w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
  <w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>
</w:numbering>'''


def content_types_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''


def package_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


def document_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''


def settings_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="{W_NS}">
  <w:zoom w:percent="100"/>
  <w:defaultTabStop w:val="720"/>
  <w:compat/>
</w:settings>'''


def header_xml():
    left = p("Software Requirements Specification", style="Footer", runs=[r("Software Requirements Specification", color="666666", size=9)])
    right = p("Deepfake Face Detector", style="Footer", runs=[r("Deepfake Face Detector", bold=True, color="2E74B5", size=9)], align="right")
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{left}{right}</w:hdr>'


def footer_xml():
    runs = [r("Deepfake Face Detector SRS | Page ", color="666666", size=9), fld_simple("PAGE")]
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{p(style="Footer", runs=runs, align="center")}</w:ftr>'


def core_xml():
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Software Requirements Specification - Deepfake Face Detector</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''


def app_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <Company></Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>1.0</AppVersion>
</Properties>'''


def build():
    if os.path.exists(OUT):
        os.remove(OUT)
    files = {
        "[Content_Types].xml": content_types_xml(),
        "_rels/.rels": package_rels_xml(),
        "word/document.xml": doc_xml(),
        "word/_rels/document.xml.rels": document_rels_xml(),
        "word/styles.xml": styles_xml(),
        "word/numbering.xml": numbering_xml(),
        "word/settings.xml": settings_xml(),
        "word/header1.xml": header_xml(),
        "word/footer1.xml": footer_xml(),
        "docProps/core.xml": core_xml(),
        "docProps/app.xml": app_xml(),
    }
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content.encode("utf-8"))
    print(os.path.abspath(OUT))


if __name__ == "__main__":
    build()
