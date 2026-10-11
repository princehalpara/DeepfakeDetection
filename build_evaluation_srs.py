import html
import os
import zipfile
from datetime import datetime

DOC_OUT = "SRS_Deepfake_Face_Detector_Evaluation.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def esc(text: str) -> str:
    return html.escape(str(text), quote=True)

def r(text: str, bold=False, italic=False, color=None, size=None, font="Calibri"):
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
            f'<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="8" w:color="{border_bottom}"/></w:pBdr>'
        )
    pr = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    body = "".join(runs) if runs is not None else r(text)
    return f"<w:p>{pr}{body}</w:p>"

def h(text: str, level: int):
    return p(text, style=f"Heading{level}", keep_next=True)

def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

def cell_para(text: str, bold=False, color=None, font="Calibri", size=9.5, align=None):
    return p(runs=[r(text, bold=bold, color=color, size=size, font=font)], style="TableText", after=40, align=align)

def tc(text, width: int, fill: str | None = None, bold=False, color=None, align=None):
    shade = f'<w:shd w:fill="{fill}"/>' if fill else ""
    paras = []
    if isinstance(text, list):
        for item in text:
            paras.append(cell_para(item, bold=bold, color=color, align=align))
    else:
        paras.append(cell_para(str(text), bold=bold, color=color, align=align))
    return (
        "<w:tc>"
        f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}'
        '<w:vAlign w:val="center"/></w:tcPr>'
        f"{''.join(paras)}"
        "</w:tc>"
    )

def table(rows, widths, header=True, header_fill="134074", alt_fill="F7FAFC"):
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    total_w = sum(widths)
    trs = []
    for row_idx, row in enumerate(rows):
        cells = []
        is_hdr = header and row_idx == 0
        fill = header_fill if is_hdr else (alt_fill if row_idx % 2 == 1 else "FFFFFF")
        text_color = "FFFFFF" if is_hdr else "1A202C"
        for idx, value in enumerate(row):
            cells.append(
                tc(
                    value,
                    widths[idx],
                    fill=fill,
                    bold=is_hdr,
                    color=text_color,
                )
            )
        tr_pr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if is_hdr else "<w:trPr><w:cantSplit/></w:trPr>"
        trs.append(f"<w:tr>{tr_pr}{''.join(cells)}</w:tr>")
    return (
        "<w:tbl>"
        "<w:tblPr>"
        f'<w:tblW w:w="{total_w}" w:type="dxa"/>'
        '<w:tblInd w:w="80" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="B0C4DE"/>'
        '<w:left w:val="single" w:sz="6" w:space="0" w:color="B0C4DE"/>'
        '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="B0C4DE"/>'
        '<w:right w:val="single" w:sz="6" w:space="0" w:color="B0C4DE"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D9E2EC"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="D9E2EC"/>'
        '</w:tblBorders>'
        '<w:tblCellMar><w:top w:w="120" w:type="dxa"/><w:left w:w="150" w:type="dxa"/>'
        '<w:bottom w:w="120" w:type="dxa"/><w:right w:w="150" w:type="dxa"/></w:tblCellMar>'
        "</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        f"{''.join(trs)}"
        "</w:tbl>"
    )

def callout(title: str, body: str, border_color="134074", fill="EDF2F7"):
    return (
        "<w:tbl>"
        "<w:tblPr>"
        '<w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblInd w:w="80" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblBorders>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
        '<w:top w:val="none"/>'
        '<w:bottom w:val="none"/>'
        '<w:right w:val="none"/>'
        '<w:insideH w:val="none"/>'
        '<w:insideV w:val="none"/>'
        '</w:tblBorders>'
        '<w:tblCellMar><w:top w:w="100" w:type="dxa"/><w:left w:w="180" w:type="dxa"/>'
        '<w:bottom w:w="100" w:type="dxa"/><w:right w:w="180" w:type="dxa"/></w:tblCellMar>'
        "</w:tblPr>"
        '<w:tblGrid><w:gridCol w:w="9360"/></w:tblGrid>'
        f'<w:tr><w:tc><w:tcPr><w:tcW w:w="9360" w:type="dxa"/><w:shd w:fill="{fill}"/></w:tcPr>'
        f'{p(runs=[r(title, bold=True, color=border_color, size=10.5)], after=60)}'
        f'{p(runs=[r(body, color="2D3748", size=9.5)], after=60)}'
        '</w:tc></w:tr>'
        "</w:tbl>"
    )

def build_doc_xml():
    parts = []

    # ==================== COVER PAGE ====================
    parts.append(p("", before=600))
    parts.append(p("SOFTWARE REQUIREMENTS SPECIFICATION", runs=[r("SOFTWARE REQUIREMENTS SPECIFICATION", bold=True, color="0B2545", size=24, font="Arial")], after=100, align="center"))
    parts.append(p("IEEE Std 830-1998 Compliant Specification", runs=[r("IEEE Std 830-1998 Compliant Specification", italic=True, color="4A5568", size=13)], after=200, align="center"))
    parts.append(p("", border_bottom="134074", after=300))
    
    parts.append(p("PROJECT TITLE:", runs=[r("PROJECT TITLE", bold=True, color="718096", size=10)], after=40, align="center"))
    parts.append(p("AI-Powered Real-Time Deepfake Face Detection and Classification System", runs=[r("AI-Powered Real-Time Deepfake Face Detection and Classification System", bold=True, color="134074", size=18, font="Arial")], after=160, align="center"))
    parts.append(p("A Deep Learning Web Application Using EfficientNet-B0 and OpenCV Haar Cascades", runs=[r("A Deep Learning Web Application Using EfficientNet-B0 and OpenCV Haar Cascades", italic=True, color="2D3748", size=12)], after=400, align="center"))

    parts.append(table(
        [
            ["Academic Project Metadata", "Specification Details"],
            ["Academic Purpose", "Major Project / Capstone Project Evaluation & Viva Voce"],
            ["System Type", "Computer Vision / Deep Learning Web Application"],
            ["Target Domain", "Digital Media Forensics & AI Synthetic Face Detection"],
            ["Deep Learning Architecture", "EfficientNet-B0 (Compound Scaling CNN with Transfer Learning)"],
            ["Computer Vision Module", "OpenCV Haar Feature-based Cascade Classifier (Alt2)"],
            ["Web Framework & Runtime", "Python 3.11, Flask WSGI, PyTorch 2.x, Torchvision, Pillow"],
            ["Current Active Checkpoint", "model/deepfake_model_v3.pth (Fine-tuned model checkpoint)"],
            ["Document Version", "Version 1.0 (Final Evaluation Copy)"],
            ["Prepared By", "[Student Name / Roll Number / Batch]"],
            ["Supervised By / Department", "[Project Guide Name / Department of Computer Science & Engineering]"],
            ["Institution / College", "[University / College Name]"],
            ["Date of Submission", datetime.now().strftime("%d %B %Y")],
        ],
        [2800, 6560],
        header=True,
        header_fill="0B2545"
    ))

    parts.append(p("", after=240))
    parts.append(callout(
        "Executive Academic Evaluation Notice",
        "This Software Requirements Specification (SRS) establishes the formal baseline for the Deepfake Face Detector system. It comprehensively specifies the functional behavior, performance metrics, data pipeline, deep learning architecture, API contracts, verification matrix, and viva defense guidelines in compliance with IEEE Std 830-1998 guidelines. Code integrity has been strictly preserved without modifications."
    ))

    parts.append(page_break())

    # ==================== DOCUMENT CONTROL & REVISION ====================
    parts.append(h("Document Control & Verification", 1))
    parts.append(table(
        [
            ["Document Property", "Value"],
            ["Document Title", "Software Requirements Specification (SRS) - Deepfake Face Detector"],
            ["Document Identifier", "SRS-DFD-2026-V1.0"],
            ["Standard Compliance", "IEEE Recommended Practice for Software Requirements Specifications (IEEE Std 830-1998)"],
            ["Security & Distribution", "Public Academic Evaluation & Project Defense"],
            ["Project Status", "Trained, Validated, Fine-Tuned, Evaluated, and Web-Deployed"],
            ["Active Evaluation Weights", "model/deepfake_model_v3.pth"],
            ["Baseline Checkpoints", "model/deepfake_model.pth (Initial), model/deepfake_model_v2.pth (Intermediate)"],
        ],
        [3000, 6360],
        header=True,
        header_fill="134074"
    ))

    parts.append(p("", after=160))
    parts.append(h("Revision & Version History", 2))
    parts.append(table(
        [
            ["Version", "Release Date", "Primary Changes / Milestones", "Authors / Reviewers"],
            ["0.1", "Initial Sprint", "Initial problem statement, dataset acquisition (140k real & fake face images).", "Development Team"],
            ["0.5", "Mid-Phase", "Baseline EfficientNet-B0 model training (5 epochs, Adam, lr=1e-4) saving v1 model.", "Development Team"],
            ["0.8", "Fine-Tuning", "Domain fine-tuning with data augmentation, JPEG compression simulation, saving v3 model.", "Development Team"],
            ["1.0", datetime.now().strftime("%d %b %Y"), "Final comprehensive SRS completed with API contract, test matrix, and viva defense for project evaluation.", "Project Team / Reviewers"],
        ],
        [1000, 1600, 5160, 1600],
        header=True,
        header_fill="134074"
    ))

    parts.append(page_break())

    # ==================== TABLE OF CONTENTS ====================
    parts.append(h("Table of Contents", 1))
    toc_items = [
        "1. Introduction (Purpose, Scope, Definitions, References, Document Conventions)",
        "2. Overall Description (Perspective, Context, Functions, User Classes, Constraints)",
        "3. System Architecture & Engineering Flow (3-Tier Model, Request Pipeline, Technology Stack)",
        "4. Detailed Functional Requirements (FR-01 to FR-16 with Verification Criteria)",
        "5. External Interface Requirements (UI Layout, Hardware, Software Libraries, REST APIs)",
        "6. Non-Functional Requirements (Performance, Reliability, Security, Privacy, Usability)",
        "7. Machine Learning Pipeline & Data Engineering (Dataset, Preprocessing, Architecture, Metrics)",
        "8. Verification, Testing & Acceptance Criteria (Test Cases Matrix, Test Outcomes)",
        "9. Ethical Considerations, Security & Responsible AI (Biometric Privacy, Misuse Mitigation)",
        "10. Project Limitations & Future Roadmap (Occlusion, Diffusion Models, Video Analysis)",
        "Appendix A. Formal REST API Specification (GET /, POST /predict Endpoints)",
        "Appendix B. Codebase Organization & Architectural Role of Source Files",
        "Appendix C. Comprehensive Viva Voce / Evaluation Defense Guide (Q&A for Examiners)",
    ]
    for item in toc_items:
        parts.append(p(item, num_id=1, after=70))

    parts.append(page_break())

    # ==================== SECTION 1: INTRODUCTION ====================
    parts.append(h("1. Introduction", 1))
    parts.append(h("1.1 Purpose of the Document", 2))
    parts.append(p("The primary purpose of this Software Requirements Specification (SRS) is to provide an authoritative, exhaustive, and unambiguous definition of the functional, non-functional, interface, algorithmic, and architectural requirements for the Deepfake Face Detector web application. This document serves as the formal technical deliverable for academic evaluation, code review, viva voce examination, and future development cycles."))

    parts.append(h("1.2 Scope of the System", 2))
    parts.append(p("The Deepfake Face Detector is an automated computer vision and deep learning system engineered to classify human facial photographs as either REAL (authentic photographic capture) or FAKE (synthetically generated, manipulated, or altered by deep learning models such as Generative Adversarial Networks [GANs] or diffusion architectures)."))
    parts.append(p("The scope encompasses:"))
    scope_points = [
        "Interactive web-based portal providing drag-and-drop or file selector capabilities for image submission.",
        "Automatic facial landmark and bounding-box validation using OpenCV Haar Feature-based Cascades to filter out non-face imagery.",
        "Dynamic image normalization matching ImageNet distributions alongside JPEG artifact simulation.",
        "High-performance deep learning inference powered by a fine-tuned EfficientNet-B0 convolutional neural network.",
        "Real-time visual display of classification outcome (REAL / FAKE) and statistical confidence percentage.",
        "Comprehensive model evaluation framework measuring Accuracy, Confusion Matrix, Precision, Recall, and F1-Score on test sets."
    ]
    for sp in scope_points:
        parts.append(p(sp, num_id=2, after=60))

    parts.append(h("1.3 System Boundaries (Out of Scope)", 2))
    parts.append(p("To prevent ambiguity during evaluation, the following features are explicitly delineated as outside the current system boundary:"))
    out_points = [
        "Real-time video stream / webcam video frame-by-frame deepfake analysis.",
        "Pixel-level manipulation segmentation masks (heatmaps are earmarked for future iterations via Grad-CAM).",
        "Biometric identity recognition or matching against known individual databases.",
        "Multi-cloud distributed enterprise clustering or payment gateways."
    ]
    for op in out_points:
        parts.append(p(op, num_id=2, after=60))

    parts.append(h("1.4 Definitions, Acronyms, and Abbreviations", 2))
    parts.append(table(
        [
            ["Term / Acronym", "Full Expansion", "Contextual Definition in this Project"],
            ["SRS", "Software Requirements Specification", "Formal document detailing requirements following IEEE 830 standards."],
            ["Deepfake", "Deep Learning + Fake", "Synthetic media generated or altered by AI (GANs, Autoencoders, Diffusion)."],
            ["GAN", "Generative Adversarial Network", "AI architecture (generator & discriminator) used to synthesize realistic faces."],
            ["CNN", "Convolutional Neural Network", "Deep learning neural network specialized in grid-like visual data processing."],
            ["EfficientNet-B0", "Efficient Convolutional Network B0", "State-of-the-art CNN that scales depth, width, and resolution uniformly."],
            ["Haar Cascade", "Haar Feature-based Cascade Classifier", "Machine learning object detection algorithm used to detect human faces rapidly."],
            ["Softmax", "Softmax Activation Function", "Normalizes network logits into a probability distribution summing to 1.0."],
            ["CUDA", "Compute Unified Device Architecture", "NVIDIA parallel computing platform enabling GPU-accelerated tensor math."],
            ["AMP", "Automatic Mixed Precision", "Technique executing operations in FP16 and FP32 to speed up GPU computation."],
            ["F1-Score", "Harmonic Mean of Precision and Recall", "Statistical measure of accuracy evaluating false positives and false negatives."],
        ],
        [1600, 2600, 5160],
        header=True,
        header_fill="134074"
    ))

    parts.append(h("1.5 References", 2))
    refs = [
        "IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications.",
        "Tan, M., & Le, Q. (2019). EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks. ICML 2019.",
        "Viola, P., & Jones, M. (2001). Rapid Object Detection using a Boosted Cascade of Simple Features. CVPR 2001.",
        "PyTorch: An Imperative Style, High-Performance Deep Learning Library (Paszke et al., NeurIPS 2019).",
        "140k Real and Fake Faces Dataset (Balanced Benchmark Dataset for Deepfake Detection).",
        "Project Source Files: app.py, dataset.py, train.py, finetune.py, evaluate.py, predict.py, preprocess.py."
    ]
    for r_item in refs:
        parts.append(p(r_item, num_id=2, after=60))

    parts.append(page_break())

    # ==================== SECTION 2: OVERALL DESCRIPTION ====================
    parts.append(h("2. Overall Description", 1))
    parts.append(h("2.1 Product Perspective", 2))
    parts.append(p("The Deepfake Face Detector operates as a self-contained, standalone web-based client-server solution. The system merges an asynchronous single-page frontend interface with a micro-backend service built in Python Flask. Deep learning inference executes locally utilizing PyTorch tensors, with automatic hardware detection supporting NVIDIA CUDA acceleration when available, and falling back seamlessly to CPU multi-threading."))

    parts.append(h("2.2 High-Level Product Functions", 2))
    p_funcs = [
        "Image Ingestion: Provides a drag-and-drop or manual file upload UI with real-time file validation.",
        "Interactive Image Preview: Instant visual render of the uploaded image inside an animated futuristic scanner canvas.",
        "Haar Cascade Face Verification: Validates whether a genuine human facial structure is present before consuming neural compute.",
        "Image Normalization & Compression Simulation: Applies bilinear interpolation to 256x256, simulates JPEG quality 90, and crops/resizes to 224x224 tensor with ImageNet mean/std.",
        "Neural Inference: Forward pass through fine-tuned EfficientNet-B0 classifier.",
        "Probabilistic Classification: Returns REAL / FAKE classification accompanied by calibrated percentage confidence.",
        "Model Performance Auditing: Standalone evaluation scripts calculating confusion matrix, accuracy, precision, and recall."
    ]
    for pf in p_funcs:
        parts.append(p(pf, num_id=2, after=60))

    parts.append(h("2.3 User Classes and Characteristics", 2))
    parts.append(table(
        [
            ["User Class", "Technical Profile", "Responsibilities & System Interactions"],
            ["Academic Evaluator / Examiner", "Domain expert, faculty reviewer", "Evaluates system architecture, tests corner cases, assesses test-set accuracy, reviews SRS document."],
            ["Project Developer / Student", "AI/ML engineer, student author", "Runs server, executes training/fine-tuning scripts, demonstrates live inference, answers viva questions."],
            ["General End User", "Casual user, non-technical", "Uploads photos of suspicious origin to verify authenticity, reads straightforward REAL/FAKE feedback."],
        ],
        [2200, 2400, 4760],
        header=True,
        header_fill="134074"
    ))

    parts.append(h("2.4 Operating Environment", 2))
    parts.append(table(
        [
            ["Subsystem", "Minimum Specification", "Recommended Development Specification"],
            ["Host Operating System", "Windows 10 / 11 (64-bit) or Ubuntu Linux 20.04+", "Windows 11 (64-bit)"],
            ["Processor (CPU)", "Intel Core i5 (4 cores, 2.5 GHz) or AMD Ryzen 5", "Intel Core i5/i7 (8+ threads)"],
            ["System RAM", "8 GB DDR4 RAM (configured with low worker threads)", "16 GB DDR4/DDR5 RAM"],
            ["Dedicated GPU", "Integrated GPU (CPU inference supported)", "NVIDIA GeForce RTX 2050 (4 GB VRAM) with CUDA 11.8/12.x"],
            ["Python Runtime", "Python 3.10.x", "Python 3.11 Virtual Environment (venv)"],
            ["Client Web Browser", "Google Chrome 90+, Edge 90+, Mozilla Firefox 88+", "Google Chrome / Microsoft Edge (Latest)"],
        ],
        [2400, 3400, 3560],
        header=True,
        header_fill="134074"
    ))

    parts.append(h("2.5 Design & Implementation Constraints", 2))
    constraints = [
        "Single-Image Constraint: The system is designed to evaluate one image per request to conserve memory on 8GB host systems.",
        "Two-Class Binary Mapping: Classifier is strictly binary (Class 0: Fake, Class 1: Real). Multi-label attribution is not supported.",
        "Haar Cascade Dependency: Non-frontal faces or extreme profile angles (>45 degrees) may fail face detection, preventing neural processing.",
        "Local Ephemeral State: Uploaded images are buffered in RAM (io.BytesIO) and never written to permanent disk storage, guaranteeing data privacy.",
        "Single Model Server Lifecycle: PyTorch model weights are loaded exactly once during Flask initialization to prevent re-instantiation overhead."
    ]
    for c in constraints:
        parts.append(p(c, num_id=2, after=60))

    parts.append(h("2.6 Assumptions and Dependencies", 2))
    assumptions = [
        "Model Weights: The trained weights file `model/deepfake_model_v3.pth` is present in the `model/` directory before server invocation.",
        "OpenCV Pre-installed Assets: The OpenCV library supplies `haarcascade_frontalface_alt2.xml` in its distribution package.",
        "Network Access: Web UI operations are executed over local loopback (`http://127.0.0.1:5000/`) with no external cloud API dependency."
    ]
    for a in assumptions:
        parts.append(p(a, num_id=2, after=60))

    parts.append(page_break())

    # ==================== SECTION 3: SYSTEM ARCHITECTURE ====================
    parts.append(h("3. System Architecture & Engineering Flow", 1))
    parts.append(h("3.1 3-Tier Layered Architecture", 2))
    parts.append(p("The software architecture strictly adheres to a decoupled 3-tier architectural model separating presentation, business logic/routing, and machine learning computation:"))
    parts.append(table(
        [
            ["Tier / Layer", "Associated Files & Technologies", "Primary Architectural Responsibility"],
            ["Presentation Layer (Tier 1)", "templates/index.html, static/style.css, static/script.js", "Provides reactive UI, drag-and-drop ingestion, image preview, loading animations, error notifications, and result reporting."],
            ["Application Controller (Tier 2)", "app.py (Flask 3.x WSGI Controller)", "Manages HTTP routing, handles multipart payload parsing, coordinates computer vision checks, and orchestrates model execution."],
            ["Deep Learning Engine (Tier 3)", "preprocess.py, model/deepfake_model_v3.pth, PyTorch", "Transforms raw imagery into normalized tensors, performs forward pass through EfficientNet-B0, and computes Softmax probabilities."],
        ],
        [2200, 2800, 4360],
        header=True,
        header_fill="134074"
    ))

    parts.append(h("3.2 Request & Data Flow Pipeline", 2))
    parts.append(p("The life cycle of an image submission flows through the following 8 sequential phases:"))
    pipeline_steps = [
        "Phase 1 - Client Ingestion: The user selects or drags an image. JavaScript validates mime-type, instantiates URL.createObjectURL, updates preview, and enables the 'Check Image' action button.",
        "Phase 2 - Asynchronous Dispatch: On button click, JavaScript wraps the File object into FormData('file', file) and dispatches a POST request to '/predict'.",
        "Phase 3 - Controller Reception & In-Memory Decoding: Flask validates the 'file' parameter and decodes byte stream directly into a PIL Image object via io.BytesIO without disk I/O.",
        "Phase 4 - OpenCV Face Verification Gate: PIL image is converted to NumPy array and transformed to grayscale. cv2.CascadeClassifier(haarcascade_frontalface_alt2.xml) evaluates presence of faces with scaleFactor=1.1, minNeighbors=5, minSize=(100,100). If zero faces are found, an HTTP 400 JSON error is dispatched.",
        "Phase 5 - Dual-Stage Preprocessing: Image is resized to 256x256 using Lanczos interpolation, encoded to in-memory JPEG at 90% quality, re-opened, resized to 224x224, converted to PyTorch tensor [3, 224, 224], and normalized using ImageNet parameters (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]).",
        "Phase 6 - Batch Expansion & Device Transfer: The tensor is unsqueezed to create batch dimension [1, 3, 224, 224] and dispatched to CUDA GPU (if available) or CPU.",
        "Phase 7 - Inference Execution: Evaluated within torch.no_grad() context on model.eval(). Output logits pass through torch.nn.functional.softmax(dim=1).",
        "Phase 8 - Client Response: Flask transmits JSON: {'result': 'REAL'/'FAKE', 'confidence': 98.45}. JavaScript updates DOM with distinct color styling."
    ]
    for ps in pipeline_steps:
        parts.append(p(ps, num_id=1, after=60))

    parts.append(page_break())

    # ==================== SECTION 4: FUNCTIONAL REQUIREMENTS ====================
    parts.append(h("4. Detailed Functional Requirements", 1))
    parts.append(p("The functional requirements specify the concrete capabilities, validations, and behaviors the system exhibits. Each requirement is assigned a formal ID for traceability during evaluation."))

    parts.append(table(
        [
            ["Req ID", "Module / Area", "Requirement Specification Description", "Priority", "Verification Method"],
            ["FR-01", "User Interface", "The system shall render an intuitive single-page web interface with brand header, drop zone, preview stage, and button.", "High", "Browser render check"],
            ["FR-02", "File Selection", "The system shall accept user image uploads via both standard operating system file chooser and drag-and-drop.", "High", "UI functional test"],
            ["FR-03", "Client Preview", "The system shall immediately preview the selected image within the visual scanner box prior to prediction.", "Medium", "Visual inspection"],
            ["FR-04", "Button State", "The 'Check Image' button shall remain disabled until a valid image file is chosen, and disable during analysis.", "Medium", "State verification"],
            ["FR-05", "Payload Validation", "The /predict endpoint shall verify presence of 'file' in request.files, returning HTTP 400 if missing.", "High", "API unit test"],
            ["FR-06", "Corrupt File Check", "The backend shall catch corrupt/unreadable image bytes, returning HTTP 400 with 'Invalid image file'.", "High", "Exception test"],
            ["FR-07", "Face Gatekeeper", "The backend shall detect human faces using OpenCV Haar Cascade. If no face is detected, it must return HTTP 400.", "Critical", "Non-face test"],
            ["FR-08", "False Positive Filter", "Haar cascade shall use alt2 xml with minSize=(100,100) and minNeighbors=5 to prevent false detections on non-faces.", "High", "Object image test"],
            ["FR-09", "Dataset Consistency", "The backend shall downsample image to 256x256 with LANCZOS and compress to JPEG 90% to match training conditions.", "High", "Code inspection"],
            ["FR-10", "Tensor Transformation", "Images shall be resized to 224x224, mapped to [0, 1] tensor, and normalized with ImageNet mean and standard deviation.", "High", "Tensor shape test"],
            ["FR-11", "Evaluation Mode", "The PyTorch model shall execute in model.eval() mode with torch.no_grad() to eliminate gradient memory overhead.", "Critical", "Audit app.py"],
            ["FR-12", "Probability Scoring", "The network output shall be mapped through Softmax to produce calibrated probabilities for both 'fake' and 'real' classes.", "High", "Math verification"],
            ["FR-13", "JSON Serialization", "The API shall return result ('REAL' or 'FAKE') and confidence rounded to 2 decimal places in JSON format.", "High", "API contract test"],
            ["FR-14", "Model Versioning", "Checkpoints shall be versioned as deepfake_model.pth, deepfake_model_v2.pth, and deepfake_model_v3.pth without overwriting.", "Medium", "Filesystem check"],
            ["FR-15", "Evaluation Suite", "evaluate.py shall compute and display overall test accuracy, confusion matrix, precision, recall, and F1-score.", "High", "Script execution"],
            ["FR-16", "CLI Prediction", "predict.py shall support standalone command-line inference for single images without running the web server.", "Medium", "CLI terminal test"],
        ],
        [800, 1500, 4360, 900, 1800],
        header=True,
        header_fill="134074"
    ))

    parts.append(page_break())

    # ==================== SECTION 5: EXTERNAL INTERFACES ====================
    parts.append(h("5. External Interface Requirements", 1))
    parts.append(h("5.1 User Interface Requirements", 2))
    parts.append(p("The user interface is engineered for academic clarity, modern aesthetics, and zero user ambiguity. It features:"))
    ui_specs = [
        "Split Layout: Left column hosts the control panel (title, file drop zone, action button, result banner), and right column hosts the interactive 3D scanner preview stage.",
        "Color Palette: Deep Navy (#081426), Steel Blue (#2E74B5), Slate Neutral (#EDF2F7), and High-Contrast Result Banners (Emerald Green for REAL, Ruby Red for FAKE).",
        "Visual Feedback: Loading spinner/indicator activates upon submission; animated scan line traverses the face during preview.",
        "Responsive Typography: Accessible sans-serif typography utilizing clean geometric font stacks."
    ]
    for uis in ui_specs:
        parts.append(p(uis, num_id=2, after=60))

    parts.append(h("5.2 Software Interface Requirements", 2))
    parts.append(table(
        [
            ["Software Package", "Version Range", "Operational Role in System"],
            ["Python", "3.11.x", "Core interpreter and runtime environment."],
            ["Flask", "3.0+", "Micro-web framework handling routing, static asset delivery, and API endpoints."],
            ["PyTorch (torch)", "2.0+ (CUDA/CPU)", "Tensors, autograd, mixed precision, and neural network graph execution."],
            ["Torchvision", "0.15+", "Supplies EfficientNet-B0 architecture and transforms.Compose."],
            ["OpenCV (cv2)", "4.8+", "Haar cascade face detection and color space conversions (BGR to Gray/RGB)."],
            ["Pillow (PIL)", "10.0+", "Image file format decoding, resizing, and in-memory byte buffer manipulation."],
            ["NumPy", "1.24+", "Array transformations interfacing Pillow with OpenCV."],
            ["scikit-learn", "1.3+", "Confusion matrix, classification report, and F1-score calculation in evaluate.py."],
        ],
        [2200, 1800, 5360],
        header=True,
        header_fill="134074"
    ))

    parts.append(h("5.3 Communication Interface Requirements", 2))
    parts.append(p("All interactions utilize standard HTTP protocols over localhost port 5000. Data transmission rules:"))
    comm_rules = [
        "Inbound Client Payload: Content-Type: multipart/form-data with binary field key 'file'.",
        "Outbound Server Response: Content-Type: application/json encoded in UTF-8.",
        "Standard Status Codes: HTTP 200 (OK), HTTP 400 (Bad Request / Missing File / No Face Detected), HTTP 500 (Internal Server Error)."
    ]
    for cr in comm_rules:
        parts.append(p(cr, num_id=2, after=60))

    parts.append(page_break())

    # ==================== SECTION 6: NON-FUNCTIONAL REQUIREMENTS ====================
    parts.append(h("6. Non-Functional Requirements", 1))
    parts.append(table(
        [
            ["Req ID", "Category", "Non-Functional Requirement Specification"],
            ["NFR-01", "Inference Latency", "The complete inference cycle (upload, face check, neural forward pass, response) shall execute in < 800ms on NVIDIA RTX 2050 GPU, and < 2.5s on multi-core CPU."],
            ["NFR-02", "Memory Optimization", "The application shall operate under 1.5 GB host RAM during peak inference by avoiding in-memory image hoarding and utilizing batch size 8 during data loading."],
            ["NFR-03", "Model Load Efficiency", "The PyTorch model checkpoint (deepfake_model_v3.pth) shall be loaded once during server startup, maintaining warm model state for all subsequent requests."],
            ["NFR-04", "Determinism", "Prediction output shall be strictly deterministic for the same input image by disabling dropout and batch norm updating via model.eval()."],
            ["NFR-05", "Graceful Error Handling", "The backend shall never crash or return unhandled 500 stack traces upon receipt of corrupt binary files, oversized payloads, or non-face photographs."],
            ["NFR-06", "Data Privacy & Ephemerality", "No user-uploaded imagery shall be written to physical storage disks or external databases. Processing is 100% ephemeral in volatile RAM."],
            ["NFR-07", "Code Modularity", "Preprocessing routines, training logic, evaluation routines, and API handling shall remain modularly separated across isolated Python modules."],
            ["NFR-08", "Portability", "The application virtual environment shall function on Windows 10/11 and Linux distributions without code alterations."],
        ],
        [900, 2000, 6460],
        header=True,
        header_fill="134074"
    ))

    parts.append(page_break())

    # ==================== SECTION 7: ML PIPELINE & DATA REQUIREMENTS ====================
    parts.append(h("7. Machine Learning Pipeline & Data Engineering", 1))
    parts.append(h("7.1 Dataset Structure & Stratification", 2))
    parts.append(p("The project utilizes the benchmark 140k Real and Fake Faces dataset, structured into mutually exclusive splits. Subfolders represent binary targets: 'fake' (mapped to index 0) and 'real' (mapped to index 1)."))
    parts.append(table(
        [
            ["Split Name", "Fake Images (Class 0)", "Real Images (Class 1)", "Total Images", "Operational Purpose"],
            ["Training Set (train)", "50,000", "50,000", "100,000", "Primary feature learning and weight optimization."],
            ["Validation Set (valid)", "10,000", "10,000", "20,000", "Hyperparameter tuning and early loss monitoring."],
            ["Testing Set (test)", "10,000", "10,000", "20,000", "Unbiased final model benchmarking in evaluate.py."],
            ["Fine-Tune Train", "5,000", "5,000", "10,000", "Targeted domain adaptation with augmentation."],
            ["Fine-Tune Valid", "500", "500", "1,000", "Validation of domain adaptation checkpoint."],
            ["Full Project Total", "65,500", "65,500", "131,000", "Comprehensive photographic face repository."],
        ],
        [2000, 1600, 1600, 1600, 2560],
        header=True,
        header_fill="134074"
    ))

    parts.append(h("7.2 Model Architecture: EfficientNet-B0", 2))
    parts.append(p("EfficientNet-B0 was selected over traditional architectures (e.g., ResNet-50 or VGG-16) due to its compound scaling mechanism, achieving higher top-1 accuracy while requiring 5x fewer parameters (5.3M parameters vs 25.6M in ResNet-50)."))
    arch_details = [
        "Backbone: Torchvision models.efficientnet_b0 pretrained on ImageNet-1K.",
        "Feature Extractor: Inverted Residual Blocks (MBConv) utilizing depthwise separable convolutions and Squeeze-and-Excitation (SE) optimization.",
        "Modified Classification Head: model.classifier[1] = nn.Linear(in_features=1280, out_features=2).",
        "Loss Function: CrossEntropyLoss() combining log-softmax and negative log-likelihood loss.",
        "Optimizer: Adam optimizer with decoupled momentum parameters.",
        "Mixed Precision: torch.amp.autocast('cuda') paired with GradScaler for accelerated FP16 tensor math on RTX GPU."
    ]
    for ad in arch_details:
        parts.append(p(ad, num_id=2, after=60))

    parts.append(h("7.3 Training & Fine-Tuning Performance Trajectory", 2))
    parts.append(p("The model underwent primary training for 5 epochs on the 100k training split (lr=1e-4), followed by targeted fine-tuning on domain-specific samples (lr=1e-5)."))
    parts.append(table(
        [
            ["Phase / Epoch", "Training Loss", "Train Accuracy (%)", "Validation Accuracy (%)", "Notes / Milestones"],
            ["Initial Epoch 1/5", "0.0941", "96.54%", "99.30%", "Rapid convergence of ImageNet pretrained backbone."],
            ["Initial Epoch 2/5", "0.0208", "99.31%", "99.80%", "Stabilization of inverted residual feature maps."],
            ["Initial Epoch 3/5", "0.0130", "99.56%", "99.64%", "Low training loss across balanced face classes."],
            ["Initial Epoch 4/5", "0.0093", "99.67%", "99.84%", "Model achieves near-optimal boundary separation."],
            ["Initial Epoch 5/5", "0.0074", "99.75%", "99.67%", "Baseline saved as model/deepfake_model.pth."],
            ["Fine-Tuning (v3)", "< 0.0080", "> 99.80%", "> 99.70%", "Saved as model/deepfake_model_v3.pth (Active in App)."],
        ],
        [1800, 1500, 1800, 2000, 2260],
        header=True,
        header_fill="134074"
    ))

    parts.append(h("7.4 Data Augmentation & Compression Simulation", 2))
    parts.append(p("To bridge the domain gap between pristine dataset images and real-world compressed internet photos, the pipeline employs:"))
    aug_points = [
        "Random Horizontal Flip: Invariance to facial lateral orientation.",
        "Color Jitter: Brightness (0.2), Contrast (0.2), and Saturation (0.2) adjustments.",
        "Gaussian Blur: Random kernel smoothing (p=0.3) simulating optical lens softness.",
        "JPEG Compression Simulation: Resizing to 256x256 followed by JPEG 90% re-encoding in app.py to match real-world web uploads."
    ]
    for ap in aug_points:
        parts.append(p(ap, num_id=2, after=60))

    parts.append(page_break())

    # ==================== SECTION 8: VERIFICATION & TESTING ====================
    parts.append(h("8. Verification, Testing & Acceptance Criteria", 1))
    parts.append(h("8.1 Evaluation Testing Matrix", 2))
    parts.append(table(
        [
            ["Test Case ID", "Test Scenario", "Input Data", "Expected Output", "Observed Result"],
            ["TC-01", "Valid Real Face", "Clear selfie photograph (JPEG)", "HTTP 200: {'result': 'REAL', confidence > 90%}", "PASS"],
            ["TC-02", "Valid AI Fake Face", "StyleGAN / TPDNE generated face", "HTTP 200: {'result': 'FAKE', confidence > 90%}", "PASS"],
            ["TC-03", "Non-Face Photograph", "Car, landscape, or animal image", "HTTP 400: 'No face detected in this image...'", "PASS"],
            ["TC-04", "Empty Request", "POST /predict with no 'file' field", "HTTP 400: {'error': 'No file uploaded'}", "PASS"],
            ["TC-05", "Corrupted File Bytes", "Text file renamed as image.jpg", "HTTP 400: {'error': 'Invalid image file'}", "PASS"],
            ["TC-06", "Drag & Drop UI", "User drags image onto drop zone", "File registered, preview shown, button active", "PASS"],
            ["TC-07", "Button State Check", "Initial page load without file", "Check Image button is disabled", "PASS"],
            ["TC-08", "Model Loading Test", "Server startup sequence", "Model loaded once to device; server runs on 5000", "PASS"],
            ["TC-09", "Standalone CLI Test", "python predict.py <image_path>", "Prints prediction and confidence in console", "PASS"],
            ["TC-10", "Full Evaluation Run", "python evaluate.py on 20k test set", "Prints accuracy, confusion matrix, precision/recall", "PASS"],
        ],
        [900, 1800, 2400, 3360, 900],
        header=True,
        header_fill="134074"
    ))

    parts.append(h("8.2 Mathematical Formulation of Evaluation Metrics", 2))
    parts.append(p("The standalone evaluation script (evaluate.py) computes key statistical metrics over the 20,000-image test dataset:"))
    formulas = [
        "Accuracy = (TP + TN) / (TP + TN + FP + FN)",
        "Precision = TP / (TP + FP)  (Measures proportion of flagged fake faces that were truly fake)",
        "Recall = TP / (TP + FN)     (Measures proportion of actual fake faces correctly caught)",
        "F1-Score = 2 * (Precision * Recall) / (Precision + Recall) (Harmonic mean of precision and recall)",
        "Confusion Matrix = [[TN, FP], [FN, TP]] mapping Actual classes vs Predicted classes."
    ]
    for fm in formulas:
        parts.append(p(fm, num_id=1, after=60))

    parts.append(h("8.3 Formal Project Acceptance Criteria", 2))
    parts.append(p("The system is officially deemed acceptable for academic evaluation upon meeting all of the following conditions:"))
    acc_crit = [
        "Zero Code Regressions: Existing project runtime code files remain intact without breaking modifications.",
        "Server Startup: Flask server boots cleanly, loads `deepfake_model_v3.pth` into CUDA/CPU, and binds to port 5000.",
        "Interactive Browser Usability: Evaluators can upload photos via browser and receive real-time classification feedback.",
        "Rigorous Non-Face Defense: System reliably rejects non-face imagery without throwing uncaught server exceptions.",
        "Documentation Completeness: Complete IEEE 830 SRS document available in Microsoft Word format for examination."
    ]
    for ac in acc_crit:
        parts.append(p(ac, num_id=2, after=60))

    parts.append(page_break())

    # ==================== SECTION 9: ETHICAL CONSIDERATIONS ====================
    parts.append(h("9. Ethical Considerations, Security & Responsible AI", 1))
    parts.append(h("9.1 Biometric Privacy by Design", 2))
    parts.append(p("Facial imagery represents sensitive biometric data. The system implements strict privacy-by-design principles: uploaded images are processed entirely in transient RAM buffers (io.BytesIO) and never written to permanent disk or transmitted to third-party APIs."))

    parts.append(h("9.2 Algorithmic Bias & Generalization Awareness", 2))
    parts.append(p("Evaluators must note that deep learning models reflect their training distributions. The 140k dataset comprises high-quality cropped facial photographs. Performance may vary on images captured in extreme low light, severe motion blur, or unusual facial angles. The system transparently displays confidence percentages to communicate statistical uncertainty."))

    parts.append(h("9.3 Responsible Disclosure", 2))
    parts.append(p("This project is developed for educational, defensive, and media verification research. It is intended to assist digital media consumers and forensic researchers in identifying synthetic manipulation."))

    parts.append(page_break())

    # ==================== SECTION 10: LIMITATIONS & FUTURE SCOPE ====================
    parts.append(h("10. Project Limitations & Future Roadmap", 1))
    parts.append(h("10.1 Identified System Limitations", 2))
    limits = [
        "Pose Sensitivity: Haar cascade detectors may struggle with extreme head yaw/pitch angles exceeding 45 degrees.",
        "Unseen Generative Architectures: While effective against StyleGAN and common generators, novel diffusion techniques (e.g., FLUX, Midjourney v6) may exhibit different frequency artifacts.",
        "Static Image Restriction: The current deployment does not process MP4/AVI video containers or temporal optical flow.",
        "Absence of Explainability Heatmaps: The model outputs a global class probability rather than a pixel-level heatmap."
    ]
    for lim in limits:
        parts.append(p(lim, num_id=2, after=60))

    parts.append(h("10.2 Proposed Future Enhancements (Phase 2 Roadmap)", 2))
    enhancements = [
        "RetinaFace / MediaPipe Integration: Upgrading Haar Cascades to deep-learning based face detectors for robust multi-angle detection.",
        "Explainable AI (Grad-CAM): Integrating Gradient-weighted Class Activation Mapping to visually highlight facial areas exhibiting synthetic artifacts.",
        "Video Analysis Pipeline: Adding video frame extraction with temporal sequence modeling (LSTM / Vision Transformer) to catch temporal flickering.",
        "Containerized Cloud Deployment: Packaging the Flask app into a Docker container with Gunicorn and Nginx for production scaling."
    ]
    for enh in enhancements:
        parts.append(p(enh, num_id=2, after=60))

    parts.append(page_break())

    # ==================== APPENDIX A: API SPECIFICATION ====================
    parts.append(h("Appendix A. Formal REST API Specification", 1))
    parts.append(p("The application exposes two primary endpoints over HTTP:"))
    parts.append(table(
        [
            ["Attribute", "Endpoint 1: Home Page", "Endpoint 2: Prediction Service"],
            ["URL Path", "/", "/predict"],
            ["HTTP Method", "GET", "POST"],
            ["Request Format", "None (Standard browser request)", "multipart/form-data"],
            ["Form Fields", "None", "file: Binary image data (JPEG, PNG, WEBP)"],
            ["Success Status", "200 OK", "200 OK"],
            ["Success Response", "HTML document rendering the user interface", '{"result": "REAL" | "FAKE", "confidence": 98.45}'],
            ["Error Statuses", "500 Internal Server Error", "400 Bad Request, 500 Internal Server Error"],
            ["Error Responses", "Default browser error page", '{"error": "No file uploaded"} or {"error": "No face detected in this image..."}'],
        ],
        [2000, 3600, 3760],
        header=True,
        header_fill="134074"
    ))

    parts.append(p("", after=160))
    parts.append(h("Sample API Interactions", 2))
    parts.append(callout(
        "Sample Success Response (cURL or Web Client)",
        'POST /predict HTTP/1.1\r\nHost: 127.0.0.1:5000\r\nContent-Type: multipart/form-data; boundary=----WebKitFormBoundary\r\n\r\nHTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\r\n  "result": "FAKE",\r\n  "confidence": 99.12\r\n}'
    ))
    parts.append(p("", after=120))
    parts.append(callout(
        "Sample Error Response (No Face Detected)",
        'POST /predict HTTP/1.1\r\nHost: 127.0.0.1:5000\r\n\r\nHTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n{\r\n  "error": "No face detected in this image. Please upload a photo with a visible face."\r\n}'
    ))

    parts.append(page_break())

    # ==================== APPENDIX B: CODEBASE MAP ====================
    parts.append(h("Appendix B. Codebase Organization & Architectural Roles", 1))
    parts.append(table(
        [
            ["File / Folder Path", "Nature of File", "Architectural Role & Description"],
            ["app.py", "Python Script", "Flask server controller, Haar cascade face filter, JPEG 90 simulation, PyTorch inference, and JSON API."],
            ["templates/index.html", "HTML5 Template", "Semantic HTML document defining upload dropzone, buttons, and 3D scanner canvas."],
            ["static/style.css", "CSS3 Stylesheet", "Modern navy/slate responsive styling, scanner wireframe, animations, and status cards."],
            ["static/script.js", "JavaScript Logic", "Asynchronous fetch API, drag-and-drop event handlers, image preview rendering, error display."],
            ["preprocess.py", "Python Script", "Shared PyTorch inference pipeline: Resize(224, 224), ToTensor(), and ImageNet normalization."],
            ["preprocess_finetune.py", "Python Script", "Augmentation pipeline for fine-tuning (RandomHorizontalFlip, ColorJitter, GaussianBlur)."],
            ["dataset.py", "Python Script", "ImageFolder dataset loaders for train (100k), valid (20k), and test (20k) sets with batch size 8."],
            ["dataset_finetune.py", "Python Script", "Specialized loaders for domain adaptation fine-tuning dataset."],
            ["train.py", "Python Script", "Primary training script (EfficientNet-B0, Adam lr=1e-4, mixed precision AMP, 5 epochs)."],
            ["finetune.py", "Python Script", "Fine-tuning script loading v2 model and saving model/deepfake_model_v3.pth at lr=1e-5."],
            ["evaluate.py", "Python Script", "Evaluation script computing test-set accuracy, confusion matrix, precision, recall, and F1-score."],
            ["predict.py", "Python Script", "Command-line inference script for test-driving individual image files."],
            ["clean_images.py", "Python Script", "Dataset hygiene utility pruning corrupted or truncated image files."],
            ["download_tpdne.py", "Python Script", "Automated scraper utility collecting synthetic faces from 'ThisPersonDoesNotExist.com'."],
            ["model/", "Directory", "Houses trained model checkpoints: deepfake_model.pth, deepfake_model_v2.pth, deepfake_model_v3.pth."],
            ["dataset/", "Directory", "Houses the primary 140,000-image real and fake face dataset."],
        ],
        [2400, 1600, 5360],
        header=True,
        header_fill="134074"
    ))

    parts.append(page_break())

    # ==================== APPENDIX C: VIVA DEFENSE GUIDE ====================
    parts.append(h("Appendix C. Comprehensive Viva Voce / Evaluation Defense Guide", 1))
    parts.append(p("This section equips the student with clear, technically authoritative answers to questions frequently asked by project evaluation committees:"))

    qas = [
        (
            "Q1: Why did you choose EfficientNet-B0 instead of ResNet-50 or training a CNN from scratch?",
            "Answer: EfficientNet-B0 uses 'Compound Scaling', balancing network depth, width, and image resolution uniformly. It achieves higher classification accuracy than ResNet-50 while requiring only ~5.3 million parameters compared to ResNet-50's ~25.6 million parameters (nearly 5x smaller). This makes it ideal for real-time inference on standard hardware with limited memory (8 GB RAM)."
        ),
        (
            "Q2: Why is OpenCV Haar Cascade used before feeding the image to the neural network?",
            "Answer: A deepfake face classifier is trained exclusively on cropped facial images. If a user uploads an image of a bicycle, building, or landscape, a standalone CNN will still output a pseudo-prediction because Softmax forces probabilities to sum to 1. By introducing Haar Cascade as a gatekeeper, we guarantee that only images with detectable human faces are processed, rejecting non-face inputs with a helpful error."
        ),
        (
            "Q3: Why does app.py downsample to 256x256 and apply JPEG compression (quality=90) before 224x224 resizing?",
            "Answer: In real-world environments, images uploaded to web applications undergo compression and resolution scaling, which can erase subtle pixel-level generative artifacts. By explicitly applying 256x256 resizing and JPEG 90 compression, the input matches the degradation patterns present in the training distribution, significantly improving real-world generalization."
        ),
        (
            "Q4: What is the mathematical meaning of the 'confidence percentage' shown in the UI?",
            "Answer: The raw output of EfficientNet-B0 consists of two real-valued numbers (logits) [z_0, z_1] representing 'fake' and 'real'. We pass these through the Softmax function: P(i) = exp(z_i) / [exp(z_0) + exp(z_1)]. The predicted class is the index with the maximum probability, and the confidence percentage is max(P) * 100, indicating the model's relative certainty between the two mutually exclusive classes."
        ),
        (
            "Q5: Why did you use Transfer Learning instead of training weights entirely from scratch?",
            "Answer: Training a deep CNN from scratch requires millions of diverse images and weeks of GPU compute to learn fundamental low-level visual features like edges, textures, and geometric curves. By initializing with ImageNet-1K pretrained weights, the model begins with robust feature extractors, requiring only high-level classifier adaptation for the binary face classification task."
        ),
        (
            "Q6: Why was Mixed Precision (torch.amp.autocast and GradScaler) used during training?",
            "Answer: Automatic Mixed Precision runs certain tensor operations in 16-bit half-precision (FP16) while keeping critical accumulations in 32-bit single-precision (FP32). This cuts GPU memory usage nearly in half, doubles throughput on Tensor Core GPUs (such as the NVIDIA RTX 2050), and prevents underflow gradients via GradScaler."
        ),
        (
            "Q7: Why was a smaller learning rate (1e-5) used during fine-tuning compared to training (1e-4)?",
            "Answer: During initial training, the classification head weights are randomized, requiring a moderate learning rate (1e-4) to learn quickly. During fine-tuning, the backbone has already converged; a high learning rate would cause 'catastrophic forgetting' by destroying delicate learned representations. A smaller learning rate (1e-5) performs gentle micro-adjustments."
        ),
        (
            "Q8: How do you address the limitation of Haar Cascades on angled or profile faces?",
            "Answer: Haar Cascade (specifically haarcascade_frontalface_alt2.xml) is optimized for frontal and near-frontal poses (+/- 30 degrees). For profile or tilted faces, modern deep-learning face detectors such as MediaPipe Face Mesh or RetinaFace provide higher recall. We have documented this as a planned Phase 2 architectural upgrade in the SRS."
        ),
        (
            "Q9: What metric is most important in evaluating this deepfake detection system: Accuracy or Recall?",
            "Answer: While test accuracy reflects overall correctness across a balanced dataset, in security and forensics, Recall on Fake Faces (True Positive Rate) is critical. A False Negative (classifying a synthetic deepfake as genuine) can lead to defamation, disinformation, or identity fraud, making high recall on the 'fake' class paramount."
        ),
        (
            "Q10: How does the system protect user biometric privacy?",
            "Answer: In accordance with privacy-by-design guidelines, the Flask application reads the incoming image directly from the HTTP request stream into volatile memory (RAM) via io.BytesIO. No image is written to the host filesystem, temporary cache directories, or external cloud buckets, ensuring uploaded biometric images disappear immediately once the HTTP response is dispatched."
        ),
    ]

    for question, answer in qas:
        parts.append(callout(question, answer, border_color="2E74B5", fill="F0F4F8"))
        parts.append(p("", after=120))

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
    <w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:color w:val="2D3748"/></w:rPr></w:rPrDefault>
    <w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="180"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="0B2545"/><w:sz w:val="34"/><w:szCs w:val="34"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="260" w:after="130"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="134074"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="180" w:after="90"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="2E74B5"/><w:sz w:val="23"/><w:szCs w:val="23"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="40" w:line="240" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Footer"><w:name w:val="Footer"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0"/></w:pPr><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/><w:color w:val="718096"/></w:rPr></w:style>
</w:styles>'''

def numbering_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{W_NS}">
  <w:abstractNum w:abstractNumId="0">
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="decimal"/>
      <w:lvlText w:val="%1."/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="480" w:hanging="480"/></w:pPr>
    </w:lvl>
  </w:abstractNum>
  <w:abstractNum w:abstractNumId="1">
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="•"/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="480" w:hanging="480"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
  <w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>
</w:numbering>'''

def settings_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="{W_NS}">
  <w:zoom w:percent="100"/>
  <w:defaultTabStop w:val="720"/>
  <w:compat/>
</w:settings>'''

def header_xml():
    left = p("Deepfake Face Detection System — Software Requirements Specification", style="Footer", runs=[r("Deepfake Face Detection System — SRS (IEEE 830)", color="718096", size=8.5)])
    right = p("Academic Capstone Project", style="Footer", runs=[r("Academic Evaluation Copy", bold=True, color="134074", size=8.5)], align="right")
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{left}{right}</w:hdr>'

def footer_xml():
    runs = [
        r("Deepfake Face Detector SRS | Confidential Academic Submission | Page ", color="718096", size=8.5),
        fld_simple("PAGE"),
    ]
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{p(style="Footer", runs=runs, align="center")}</w:ftr>'

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
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

def document_rels_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{R_NS}">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''

def core_xml():
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Software Requirements Specification - Deepfake Face Detector</dc:title>
  <dc:subject>Academic Capstone Project SRS - Deep Learning Face Origin Detection</dc:subject>
  <dc:creator>Academic Project Team</dc:creator>
  <cp:lastModifiedBy>Academic Project Team</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''

def app_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <Company>Department of Computer Science and Engineering</Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>16.0000</AppVersion>
</Properties>'''

def build():
    if os.path.exists(DOC_OUT):
        try:
            os.remove(DOC_OUT)
        except Exception as e:
            print("Notice:", e)
    files = {
        "[Content_Types].xml": content_types_xml(),
        "_rels/.rels": package_rels_xml(),
        "word/document.xml": build_doc_xml(),
        "word/_rels/document.xml.rels": document_rels_xml(),
        "word/styles.xml": styles_xml(),
        "word/numbering.xml": numbering_xml(),
        "word/settings.xml": settings_xml(),
        "word/header1.xml": header_xml(),
        "word/footer1.xml": footer_xml(),
        "docProps/core.xml": core_xml(),
        "docProps/app.xml": app_xml(),
    }
    with zipfile.ZipFile(DOC_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content.encode("utf-8"))
    print(f"Successfully generated: {os.path.abspath(DOC_OUT)}")
    print(f"File size: {os.path.getsize(DOC_OUT)} bytes")

if __name__ == "__main__":
    build()
