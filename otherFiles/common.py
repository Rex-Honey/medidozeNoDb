import os, time, serial
from typing import Iterable, Optional, Union
from PyQt6.QtGui import QImage, QPixmap, QPainter, QBrush, QWindow
from PyQt6.QtCore import Qt, QRect, QStandardPaths

rootDir = os.path.dirname(os.path.dirname(__file__))
defaultUserImage = os.path.join(rootDir, "images", "user.jpg")
medidozeDir = os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation), 'medidoze')

def find_widget_recursive(parent, target_type):
    """Recursively search for a widget of type target_type inside parent."""
    if isinstance(parent, target_type):
        return parent
    if hasattr(parent, 'children'):
        for child in parent.children():
            result = find_widget_recursive(child, target_type)
            if result is not None:
                return result
    return None

def switchToPage(currentWidget, pageClass):
    try:
        from pages.pageContainer import PageContainer
        parent = currentWidget.parentWidget()
        while parent is not None:
            if hasattr(parent, "stack"):
                break
            parent = parent.parentWidget()
        if parent is not None:
            for i in range(parent.stack.count()):
                widget = parent.stack.widget(i)
                if isinstance(widget, PageContainer):
                    # Recursively search for PharmacyUsersWindow inside this PageContainer
                    if find_widget_recursive(widget, pageClass):
                        parent.stack.setCurrentWidget(widget)
                        return
            print(f"{pageClass.__name__} not found in stack!")
        else:
            print("Main stack not found!")
    except Exception as e:
        print(e)

def dictfetchall(cursor):
    '''
    Return all rows from a cursor as a dict
    Make sure that columns name should be different
    '''
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def setState(widget, state):
    widget.setProperty("ok", state == "ok")
    widget.setProperty("error", state == "err")
    widget.setProperty("disabled", state == "disable")
    widget.style().unpolish(widget)
    widget.style().polish(widget)

def roundImage(imgdata, imgtype='jpg', size=120):
            """Return a ``QPixmap`` from *imgdata* masked with a smooth circle.

            *imgdata* are the raw image bytes, *imgtype* denotes the image type.

            The returned image will have a size of *size* × *size* pixels.

            """
            # Load image and convert to 32-bit ARGB (adds an alpha channel)
            image = QImage.fromData(imgdata, imgtype)
            image.convertToFormat(QImage.Format.Format_ARGB32)

            # Crop image to a square
            imgsize = min(image.width(), image.height())
            rect = QRect(
                int((image.width() - imgsize) / 2),
                int((image.height() - imgsize) / 2),
                imgsize,
                imgsize,
            )

            image = image.copy(rect)

            # Create the output image with the same dimensions and an alpha channel
            # and make it completely transparent
            out_img = QImage(imgsize, imgsize, QImage.Format.Format_ARGB32)
            out_img.fill(Qt.GlobalColor.transparent)

            # Create a texture brush and paint a circle with the original image onto
            # the output image
            brush = QBrush(image)  # Create texture brush
            painter = QPainter(out_img)  # Paint the output image
            painter.setBrush(brush)  # Use the image texture brush
            # pen = QPen(Qt.GlobalColor.transparent) # Don't draw an outline
            painter.setPen(Qt.PenStyle.NoPen)
            # painter.setPen(Qt.NoPen)  # Don't draw an outline
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Use AA
            painter.drawEllipse(0, 0, imgsize, imgsize)  # Actually draw the circle
            painter.end()  # We are done (segfault if you forget this)

            # Convert the image to a pixmap and rescale it.  Take pixel ratio into
            # account to get a sharp image on retina displays
            pr = QWindow().devicePixelRatio()
            pm = QPixmap.fromImage(out_img)
            pm.setDevicePixelRatio(pr)
            size *= int(pr)
            pm = pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            return pm


def sendPcbCommand(
    port: Optional[str],
    command: str,
    *,
    baudRate: int = 115200,
    readTimeout: float = 1.0,
    writeTimeout: float = 2.0,
    maxEmptyReads: int = 3,
    maxDuration: float = 8.0,
    errorKeywords: Optional[Iterable[str]] = None,
    logCommand: bool = False,
) -> Union[str, Exception]:
    try:
        if not port:
            return

        if logCommand:
            print(command)

        payload = f"{command.strip()}\n".encode("utf-8")
        with serial.Serial(
            port,
            baudRate,
            timeout=readTimeout,
            write_timeout=writeTimeout,
        ) as ser:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(payload)
            ser.flush()
            time.sleep(0.05)

            responses = []
            emptyReads = 0
            startTime = time.monotonic()

            while time.monotonic() - startTime < maxDuration:
                rawResponse = ser.readline()
                if not rawResponse:
                    emptyReads += 1
                    if emptyReads >= maxEmptyReads:
                        print("sendPcbCommand: reached empty read limit")
                        break
                    continue

                emptyReads = 0
                response = rawResponse.decode("utf-8", errors="ignore").strip()
                if not response:
                    continue

                responses.append(response)
                print(f"sendPcbCommand response {len(responses)} -- {response}")
        return "Success"
    except Exception as error:
        print("sendPcbCommand error", error)
        return error
