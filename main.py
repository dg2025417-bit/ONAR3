import base64
import io
import os
import tempfile
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageOps

st.set_page_config(page_title="포토부스", page_icon="📸", layout="centered")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# Camera widget: a Streamlit custom component written in plain HTML/JS.
# The HTML/JS source is stored below as base64 text (not a raw triple-quoted
# string) so that copy/pasting this file through a text editor can never
# corrupt it -- base64 only contains letters, digits, "+", "/", "=", so
# stray quote/whitespace changes during paste cannot break the file.
# --------------------------------------------------------------------------
_CAMERA_HTML_B64 = (
    "PCFET0NUWVBFIGh0bWw+CjxodG1sIGxhbmc9ImtvIj4KPGhlYWQ+CjxtZXRhIGNoYXJzZXQ9IlVURi04IiAvPgo8c3R5bGU+CiAg"
    "aHRtbCwgYm9keSB7CiAgICBtYXJnaW46IDA7IHBhZGRpbmc6IDA7CiAgICBiYWNrZ3JvdW5kOiAjMDAwOwogICAgZm9udC1mYW1p"
    "bHk6IC1hcHBsZS1zeXN0ZW0sIEJsaW5rTWFjU3lzdGVtRm9udCwgIlNlZ29lIFVJIiwgIk1hbGd1biBHb3RoaWMiLCBzYW5zLXNl"
    "cmlmOwogICAgb3ZlcmZsb3c6IGhpZGRlbjsKICB9CiAgI3N0YWdlIHsKICAgIHBvc2l0aW9uOiByZWxhdGl2ZTsKICAgIHdpZHRo"
    "OiAxMDAlOwogICAgaGVpZ2h0OiB2YXIoLS1zdGFnZS1oZWlnaHQsIDcwMHB4KTsKICAgIGJhY2tncm91bmQ6ICMxMTE7CiAgICBk"
    "aXNwbGF5OiBmbGV4OwogICAgYWxpZ24taXRlbXM6IGNlbnRlcjsKICAgIGp1c3RpZnktY29udGVudDogY2VudGVyOwogICAgb3Zl"
    "cmZsb3c6IGhpZGRlbjsKICB9CiAgdmlkZW8gewogICAgcG9zaXRpb246IGFic29sdXRlOwogICAgdG9wOiA1MCU7IGxlZnQ6IDUw"
    "JTsKICAgIG1pbi13aWR0aDogMTAwJTsgbWluLWhlaWdodDogMTAwJTsKICAgIHdpZHRoOiBhdXRvOyBoZWlnaHQ6IGF1dG87CiAg"
    "ICB0cmFuc2Zvcm06IHRyYW5zbGF0ZSgtNTAlLCAtNTAlKSBzY2FsZVgoLTEpOyAvKiBtaXJyb3IgbGlrZSBhIG1pcnJvciAqLwog"
    "ICAgb2JqZWN0LWZpdDogY292ZXI7CiAgfQogIC8qIGRhcmsgb3ZlcmxheSB3aXRoIGEgdHJhbnNwYXJlbnQgIndpbmRvdyIgY3V0"
    "IG91dCBpbiB0aGUgbWlkZGxlLAogICAgIHNvIHRoZSBjYW1lcmEgaXMgb25seSBjbGVhcmx5IHZpc2libGUgdGhyb3VnaCB0aGUg"
    "ZnJhbWUncyBwaG90byBzbG90ICovCiAgI2ZyYW1lV2luZG93IHsKICAgIHBvc2l0aW9uOiByZWxhdGl2ZTsKICAgIHotaW5kZXg6"
    "IDU7CiAgICBib3gtc2hhZG93OiAwIDAgMCA5OTk5cHggcmdiYSgwLDAsMCwwLjYyKTsKICAgIGJvcmRlcjogM3B4IHNvbGlkIHJn"
    "YmEoMjU1LDI1NSwyNTUsMC45KTsKICAgIGJvcmRlci1yYWRpdXM6IDEwcHg7CiAgfQogICNjb3VudGRvd24gewogICAgcG9zaXRp"
    "b246IGFic29sdXRlOwogICAgei1pbmRleDogMjA7CiAgICB0b3A6IDA7IGxlZnQ6IDA7IHJpZ2h0OiAwOyBib3R0b206IDA7CiAg"
    "ICBkaXNwbGF5OiBub25lOwogICAgYWxpZ24taXRlbXM6IGNlbnRlcjsKICAgIGp1c3RpZnktY29udGVudDogY2VudGVyOwogICAg"
    "Zm9udC1zaXplOiAxNDBweDsKICAgIGZvbnQtd2VpZ2h0OiA4MDA7CiAgICBjb2xvcjogI2ZmZjsKICAgIHRleHQtc2hhZG93OiAw"
    "IDRweCAyNHB4IHJnYmEoMCwwLDAsMC42KTsKICB9CiAgI2ZsYXNoIHsKICAgIHBvc2l0aW9uOiBhYnNvbHV0ZTsKICAgIHotaW5k"
    "ZXg6IDMwOwogICAgdG9wOjA7IGxlZnQ6MDsgcmlnaHQ6MDsgYm90dG9tOjA7CiAgICBiYWNrZ3JvdW5kOiAjZmZmOwogICAgb3Bh"
    "Y2l0eTogMDsKICAgIHBvaW50ZXItZXZlbnRzOiBub25lOwogICAgdHJhbnNpdGlvbjogb3BhY2l0eSAwLjEycyBlYXNlLW91dDsK"
    "ICB9CiAgI3RvcGJhciB7CiAgICBwb3NpdGlvbjogYWJzb2x1dGU7CiAgICB0b3A6IDE0cHg7IGxlZnQ6IDA7IHJpZ2h0OiAwOwog"
    "ICAgei1pbmRleDogMTU7CiAgICBkaXNwbGF5OiBmbGV4OwogICAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7CiAgfQogICNjb3Vu"
    "dGVyIHsKICAgIGJhY2tncm91bmQ6IHJnYmEoMCwwLDAsMC41NSk7CiAgICBjb2xvcjogI2ZmZjsKICAgIHBhZGRpbmc6IDZweCAx"
    "OHB4OwogICAgYm9yZGVyLXJhZGl1czogOTk5cHg7CiAgICBmb250LXNpemU6IDE1cHg7CiAgICBsZXR0ZXItc3BhY2luZzogMC41"
    "cHg7CiAgfQogICNib3R0b21iYXIgewogICAgcG9zaXRpb246IGFic29sdXRlOwogICAgYm90dG9tOiAyMnB4OyBsZWZ0OiAwOyBy"
    "aWdodDogMDsKICAgIHotaW5kZXg6IDE1OwogICAgZGlzcGxheTogZmxleDsKICAgIGp1c3RpZnktY29udGVudDogY2VudGVyOwog"
    "ICAgZ2FwOiAxMnB4OwogIH0KICBidXR0b24uY3RybCB7CiAgICBiYWNrZ3JvdW5kOiAjZmZmOwogICAgY29sb3I6ICMxMTE7CiAg"
    "ICBib3JkZXI6IG5vbmU7CiAgICBib3JkZXItcmFkaXVzOiA5OTlweDsKICAgIHBhZGRpbmc6IDE0cHggMzRweDsKICAgIGZvbnQt"
    "c2l6ZTogMTdweDsKICAgIGZvbnQtd2VpZ2h0OiA3MDA7CiAgICBjdXJzb3I6IHBvaW50ZXI7CiAgICBib3gtc2hhZG93OiAwIDRw"
    "eCAxNHB4IHJnYmEoMCwwLDAsMC4zNSk7CiAgfQogIGJ1dHRvbi5jdHJsOmFjdGl2ZSB7IHRyYW5zZm9ybTogc2NhbGUoMC45Nyk7"
    "IH0KICBidXR0b24uc2Vjb25kYXJ5IHsKICAgIGJhY2tncm91bmQ6IHJnYmEoMjU1LDI1NSwyNTUsMC4xNSk7CiAgICBjb2xvcjog"
    "I2ZmZjsKICAgIGJvcmRlcjogMXB4IHNvbGlkIHJnYmEoMjU1LDI1NSwyNTUsMC42KTsKICB9CiAgI3N0YXR1cyB7CiAgICBwb3Np"
    "dGlvbjogYWJzb2x1dGU7CiAgICB6LWluZGV4OiAxNTsKICAgIGJvdHRvbTogOTBweDsKICAgIGxlZnQ6IDA7IHJpZ2h0OiAwOwog"
    "ICAgdGV4dC1hbGlnbjogY2VudGVyOwogICAgY29sb3I6ICNmZmY7CiAgICBmb250LXNpemU6IDE0cHg7CiAgICBvcGFjaXR5OiAw"
    "Ljg1OwogIH0KPC9zdHlsZT4KPC9oZWFkPgo8Ym9keT4KCjxkaXYgaWQ9InN0YWdlIj4KICA8dmlkZW8gaWQ9InZpZGVvIiBhdXRv"
    "cGxheSBwbGF5c2lubGluZSBtdXRlZD48L3ZpZGVvPgogIDxkaXYgaWQ9ImZyYW1lV2luZG93Ij48L2Rpdj4KICA8ZGl2IGlkPSJj"
    "b3VudGRvd24iPjwvZGl2PgogIDxkaXYgaWQ9ImZsYXNoIj48L2Rpdj4KICA8ZGl2IGlkPSJ0b3BiYXIiPjxkaXYgaWQ9ImNvdW50"
    "ZXIiPuy0rOyYgSDrjIDquLAg7KSRPC9kaXY+PC9kaXY+CiAgPGRpdiBpZD0ic3RhdHVzIj48L2Rpdj4KICA8ZGl2IGlkPSJib3R0"
    "b21iYXIiPgogICAgPGJ1dHRvbiBjbGFzcz0iY3RybCBzZWNvbmRhcnkiIGlkPSJmdWxsc2NyZWVuQnRuIiB0eXBlPSJidXR0b24i"
    "PuyghOyytO2ZlOuptDwvYnV0dG9uPgogICAgPGJ1dHRvbiBjbGFzcz0iY3RybCIgaWQ9InN0YXJ0QnRuIiB0eXBlPSJidXR0b24i"
    "Puy0rOyYgSDsi5zsnpE8L2J1dHRvbj4KICA8L2Rpdj4KPC9kaXY+Cgo8Y2FudmFzIGlkPSJjYW52YXMiIHN0eWxlPSJkaXNwbGF5"
    "Om5vbmU7Ij48L2NhbnZhcz4KCjxzY3JpcHQ+CiAgY29uc3QgU0VUX0NPTVBPTkVOVF9WQUxVRSA9ICJzdHJlYW1saXQ6c2V0Q29t"
    "cG9uZW50VmFsdWUiOwogIGNvbnN0IFJFTkRFUiA9ICJzdHJlYW1saXQ6cmVuZGVyIjsKICBjb25zdCBDT01QT05FTlRfUkVBRFkg"
    "PSAic3RyZWFtbGl0OmNvbXBvbmVudFJlYWR5IjsKICBjb25zdCBTRVRfRlJBTUVfSEVJR0hUID0gInN0cmVhbWxpdDpzZXRGcmFt"
    "ZUhlaWdodCI7CgogIGZ1bmN0aW9uIF9zZW5kTWVzc2FnZSh0eXBlLCBkYXRhKSB7CiAgICBjb25zdCBvdXRib3VuZERhdGEgPSBP"
    "YmplY3QuYXNzaWduKHsgaXNTdHJlYW1saXRNZXNzYWdlOiB0cnVlLCB0eXBlOiB0eXBlIH0sIGRhdGEpOwogICAgd2luZG93LnBh"
    "cmVudC5wb3N0TWVzc2FnZShvdXRib3VuZERhdGEsICIqIik7CiAgfQoKICBmdW5jdGlvbiBzZXRGcmFtZUhlaWdodChoZWlnaHQp"
    "IHsKICAgIF9zZW5kTWVzc2FnZShTRVRfRlJBTUVfSEVJR0hULCB7IGhlaWdodDogaGVpZ2h0IH0pOwogIH0KCiAgZnVuY3Rpb24g"
    "bm90aWZ5SG9zdCh2YWx1ZSkgewogICAgX3NlbmRNZXNzYWdlKFNFVF9DT01QT05FTlRfVkFMVUUsIHsgdmFsdWU6IHZhbHVlLCBk"
    "YXRhVHlwZTogImpzb24iIH0pOwogIH0KCiAgbGV0IGFzcGVjdFJhdGlvID0gMS4wOwogIGxldCB0b3RhbFNob3RzID0gNDsKICBs"
    "ZXQgc3RhZ2VIZWlnaHQgPSA3MDA7CiAgbGV0IHZpZGVvU3RyZWFtID0gbnVsbDsKICBsZXQgY2FwdHVyZWRQaG90b3MgPSBbXTsK"
    "ICBsZXQgc2VxdWVuY2VSdW5uaW5nID0gZmFsc2U7CiAgbGV0IGluaXRpYWxpemVkID0gZmFsc2U7CgogIGZ1bmN0aW9uIG9uUmVu"
    "ZGVyKGFyZ3MpIHsKICAgIGlmICghYXJncykgcmV0dXJuOwogICAgYXNwZWN0UmF0aW8gPSBhcmdzLmFzcGVjdFJhdGlvIHx8IDEu"
    "MDsKICAgIHRvdGFsU2hvdHMgPSBhcmdzLnNob3RzIHx8IDQ7CiAgICBzdGFnZUhlaWdodCA9IGFyZ3MuaGVpZ2h0IHx8IDcwMDsK"
    "ICAgIGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzdGFnZSIpLnN0eWxlLnNldFByb3BlcnR5KCItLXN0YWdlLWhlaWdodCIsIHN0"
    "YWdlSGVpZ2h0ICsgInB4Iik7CiAgICBsYXlvdXRXaW5kb3coKTsKICAgIGlmICghaW5pdGlhbGl6ZWQpIHsKICAgICAgaW5pdGlh"
    "bGl6ZWQgPSB0cnVlOwogICAgICBpbml0Q2FtZXJhKCk7CiAgICB9CiAgfQoKICB3aW5kb3cuYWRkRXZlbnRMaXN0ZW5lcigibWVz"
    "c2FnZSIsIChldmVudCkgPT4gewogICAgaWYgKGV2ZW50LmRhdGEudHlwZSA9PT0gUkVOREVSKSB7CiAgICAgIG9uUmVuZGVyKGV2"
    "ZW50LmRhdGEuYXJncyk7CiAgICB9CiAgfSk7CgogIHdpbmRvdy5hZGRFdmVudExpc3RlbmVyKCJyZXNpemUiLCAoKSA9PiB7CiAg"
    "ICBsYXlvdXRXaW5kb3coKTsKICAgIHNldEZyYW1lSGVpZ2h0KGRvY3VtZW50LmRvY3VtZW50RWxlbWVudC5zY3JvbGxIZWlnaHQp"
    "OwogIH0pOwoKICBmdW5jdGlvbiBsYXlvdXRXaW5kb3coKSB7CiAgICBjb25zdCBzdGFnZSA9IGRvY3VtZW50LmdldEVsZW1lbnRC"
    "eUlkKCJzdGFnZSIpOwogICAgY29uc3QgbWF4VyA9IHN0YWdlLmNsaWVudFdpZHRoICogMC44MjsKICAgIGNvbnN0IG1heEggPSBz"
    "dGFnZS5jbGllbnRIZWlnaHQgKiAwLjcyOwogICAgbGV0IHcgPSBtYXhXOwogICAgbGV0IGggPSB3IC8gYXNwZWN0UmF0aW87CiAg"
    "ICBpZiAoaCA+IG1heEgpIHsKICAgICAgaCA9IG1heEg7CiAgICAgIHcgPSBoICogYXNwZWN0UmF0aW87CiAgICB9CiAgICBjb25z"
    "dCB3aW4gPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiZnJhbWVXaW5kb3ciKTsKICAgIHdpbi5zdHlsZS53aWR0aCA9IE1hdGgu"
    "cm91bmQodykgKyAicHgiOwogICAgd2luLnN0eWxlLmhlaWdodCA9IE1hdGgucm91bmQoaCkgKyAicHgiOwogIH0KCiAgYXN5bmMg"
    "ZnVuY3Rpb24gaW5pdENhbWVyYSgpIHsKICAgIGNvbnN0IHN0YXR1c0VsID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInN0YXR1"
    "cyIpOwogICAgdHJ5IHsKICAgICAgc3RhdHVzRWwuaW5uZXJUZXh0ID0gIuy5tOuplOudvOulvCDspIDruYTtlZjripQg7KSRLi4u"
    "IjsKICAgICAgdmlkZW9TdHJlYW0gPSBhd2FpdCBuYXZpZ2F0b3IubWVkaWFEZXZpY2VzLmdldFVzZXJNZWRpYSh7CiAgICAgICAg"
    "dmlkZW86IHsgZmFjaW5nTW9kZTogInVzZXIiLCB3aWR0aDogeyBpZGVhbDogMTI4MCB9LCBoZWlnaHQ6IHsgaWRlYWw6IDEyODAg"
    "fSB9LAogICAgICAgIGF1ZGlvOiBmYWxzZSwKICAgICAgfSk7CiAgICAgIGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJ2aWRlbyIp"
    "LnNyY09iamVjdCA9IHZpZGVvU3RyZWFtOwogICAgICBzdGF0dXNFbC5pbm5lclRleHQgPSAi7KSA67mEIOyZhOujjCEg7LSs7JiB"
    "IOyLnOyekeydhCDriIzrn6zso7zshLjsmpQiOwogICAgICBzZXRUaW1lb3V0KCgpID0+IHNldEZyYW1lSGVpZ2h0KGRvY3VtZW50"
    "LmRvY3VtZW50RWxlbWVudC5zY3JvbGxIZWlnaHQpLCAyMDApOwogICAgfSBjYXRjaCAoZSkgewogICAgICBzdGF0dXNFbC5pbm5l"
    "clRleHQgPSAi7Lm066mU652866W8IOyCrOyaqe2VoCDsiJgg7JeG7Iq164uI64ukOiAiICsgZS5tZXNzYWdlICsgIiAo6raM7ZWc"
    "7J2EIO2XiOyaqe2VtOyjvOyEuOyalCkiOwogICAgfQogIH0KCiAgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImZ1bGxzY3JlZW5C"
    "dG4iKS5hZGRFdmVudExpc3RlbmVyKCJjbGljayIsICgpID0+IHsKICAgIGNvbnN0IHN0YWdlID0gZG9jdW1lbnQuZ2V0RWxlbWVu"
    "dEJ5SWQoInN0YWdlIik7CiAgICBpZiAoc3RhZ2UucmVxdWVzdEZ1bGxzY3JlZW4pIHN0YWdlLnJlcXVlc3RGdWxsc2NyZWVuKCk7"
    "CiAgICBlbHNlIGlmIChzdGFnZS53ZWJraXRSZXF1ZXN0RnVsbHNjcmVlbikgc3RhZ2Uud2Via2l0UmVxdWVzdEZ1bGxzY3JlZW4o"
    "KTsKICB9KTsKCiAgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInN0YXJ0QnRuIikuYWRkRXZlbnRMaXN0ZW5lcigiY2xpY2siLCAo"
    "KSA9PiB7CiAgICBpZiAoc2VxdWVuY2VSdW5uaW5nKSByZXR1cm47CiAgICBpZiAoIXZpZGVvU3RyZWFtKSB7CiAgICAgIGRvY3Vt"
    "ZW50LmdldEVsZW1lbnRCeUlkKCJzdGF0dXMiKS5pbm5lclRleHQgPSAi7Lm066mU65286rCAIOyVhOyngSDspIDruYTrkJjsp4Ag"
    "7JWK7JWY7Iq164uI64ukLiI7CiAgICAgIHJldHVybjsKICAgIH0KICAgIHN0YXJ0U2VxdWVuY2UoKTsKICB9KTsKCiAgZnVuY3Rp"
    "b24gc2xlZXAobXMpIHsgcmV0dXJuIG5ldyBQcm9taXNlKChyKSA9PiBzZXRUaW1lb3V0KHIsIG1zKSk7IH0KCiAgZnVuY3Rpb24g"
    "Y291bnRkb3duKG4pIHsKICAgIHJldHVybiBuZXcgUHJvbWlzZSgocmVzb2x2ZSkgPT4gewogICAgICBjb25zdCBlbCA9IGRvY3Vt"
    "ZW50LmdldEVsZW1lbnRCeUlkKCJjb3VudGRvd24iKTsKICAgICAgbGV0IGMgPSBuOwogICAgICBlbC5zdHlsZS5kaXNwbGF5ID0g"
    "ImZsZXgiOwogICAgICBlbC5pbm5lclRleHQgPSBjOwogICAgICBjb25zdCB0aW1lciA9IHNldEludGVydmFsKCgpID0+IHsKICAg"
    "ICAgICBjIC09IDE7CiAgICAgICAgaWYgKGMgPiAwKSB7CiAgICAgICAgICBlbC5pbm5lclRleHQgPSBjOwogICAgICAgIH0gZWxz"
    "ZSB7CiAgICAgICAgICBjbGVhckludGVydmFsKHRpbWVyKTsKICAgICAgICAgIGVsLmlubmVyVGV4dCA9ICLssLDsubUhIjsKICAg"
    "ICAgICAgIHNldFRpbWVvdXQoKCkgPT4geyBlbC5zdHlsZS5kaXNwbGF5ID0gIm5vbmUiOyByZXNvbHZlKCk7IH0sIDI1MCk7CiAg"
    "ICAgICAgfQogICAgICB9LCAxMDAwKTsKICAgIH0pOwogIH0KCiAgZnVuY3Rpb24gZmxhc2goKSB7CiAgICByZXR1cm4gbmV3IFBy"
    "b21pc2UoKHJlc29sdmUpID0+IHsKICAgICAgY29uc3QgZiA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJmbGFzaCIpOwogICAg"
    "ICBmLnN0eWxlLm9wYWNpdHkgPSAiMSI7CiAgICAgIHNldFRpbWVvdXQoKCkgPT4geyBmLnN0eWxlLm9wYWNpdHkgPSAiMCI7IHJl"
    "c29sdmUoKTsgfSwgMTQwKTsKICAgIH0pOwogIH0KCiAgZnVuY3Rpb24gY2FwdHVyZVBob3RvKCkgewogICAgY29uc3QgdmlkZW8g"
    "PSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgidmlkZW8iKTsKICAgIGNvbnN0IGNhbnZhcyA9IGRvY3VtZW50LmdldEVsZW1lbnRC"
    "eUlkKCJjYW52YXMiKTsKICAgIGNvbnN0IHRhcmdldFcgPSA5MDA7CiAgICBjb25zdCB0YXJnZXRIID0gTWF0aC5yb3VuZCh0YXJn"
    "ZXRXIC8gYXNwZWN0UmF0aW8pOwogICAgY2FudmFzLndpZHRoID0gdGFyZ2V0VzsKICAgIGNhbnZhcy5oZWlnaHQgPSB0YXJnZXRI"
    "OwogICAgY29uc3QgY3R4ID0gY2FudmFzLmdldENvbnRleHQoIjJkIik7CgogICAgY29uc3QgdncgPSB2aWRlby52aWRlb1dpZHRo"
    "IHx8IHRhcmdldFc7CiAgICBjb25zdCB2aCA9IHZpZGVvLnZpZGVvSGVpZ2h0IHx8IHRhcmdldEg7CiAgICBjb25zdCB2QXNwZWN0"
    "ID0gdncgLyB2aDsKICAgIGxldCBzeCwgc3ksIHN3LCBzaDsKICAgIGlmICh2QXNwZWN0ID4gYXNwZWN0UmF0aW8pIHsKICAgICAg"
    "c2ggPSB2aDsgc3cgPSB2aCAqIGFzcGVjdFJhdGlvOyBzeCA9ICh2dyAtIHN3KSAvIDI7IHN5ID0gMDsKICAgIH0gZWxzZSB7CiAg"
    "ICAgIHN3ID0gdnc7IHNoID0gdncgLyBhc3BlY3RSYXRpbzsgc3ggPSAwOyBzeSA9ICh2aCAtIHNoKSAvIDI7CiAgICB9CiAgICAv"
    "LyBtaXJyb3IgdGhlIGNhcHR1cmVkIGZyYW1lIHNvIHRoZSBzYXZlZCBwaG90byBtYXRjaGVzIHRoZSBvbi1zY3JlZW4gbWlycm9y"
    "IHByZXZpZXcKICAgIGN0eC5zYXZlKCk7CiAgICBjdHgudHJhbnNsYXRlKHRhcmdldFcsIDApOwogICAgY3R4LnNjYWxlKC0xLCAx"
    "KTsKICAgIGN0eC5kcmF3SW1hZ2UodmlkZW8sIHN4LCBzeSwgc3csIHNoLCAwLCAwLCB0YXJnZXRXLCB0YXJnZXRIKTsKICAgIGN0"
    "eC5yZXN0b3JlKCk7CgogICAgY2FwdHVyZWRQaG90b3MucHVzaChjYW52YXMudG9EYXRhVVJMKCJpbWFnZS9qcGVnIiwgMC45Mikp"
    "OwogIH0KCiAgYXN5bmMgZnVuY3Rpb24gc3RhcnRTZXF1ZW5jZSgpIHsKICAgIHNlcXVlbmNlUnVubmluZyA9IHRydWU7CiAgICBj"
    "YXB0dXJlZFBob3RvcyA9IFtdOwogICAgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInN0YXJ0QnRuIikuc3R5bGUuZGlzcGxheSA9"
    "ICJub25lIjsKICAgIGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJmdWxsc2NyZWVuQnRuIikuc3R5bGUuZGlzcGxheSA9ICJub25l"
    "IjsKICAgIGNvbnN0IGNvdW50ZXJFbCA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJjb3VudGVyIik7CiAgICBjb25zdCBzdGF0"
    "dXNFbCA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzdGF0dXMiKTsKICAgIHN0YXR1c0VsLmlubmVyVGV4dCA9ICIiOwoKICAg"
    "IGZvciAobGV0IGkgPSAwOyBpIDwgdG90YWxTaG90czsgaSsrKSB7CiAgICAgIGNvdW50ZXJFbC5pbm5lclRleHQgPSAoaSArIDEp"
    "ICsgIiAvICIgKyB0b3RhbFNob3RzICsgIiDstKzsmIEg7KSA67mEIjsKICAgICAgYXdhaXQgY291bnRkb3duKDMpOwogICAgICBj"
    "YXB0dXJlUGhvdG8oKTsKICAgICAgYXdhaXQgZmxhc2goKTsKICAgICAgY291bnRlckVsLmlubmVyVGV4dCA9IChpICsgMSkgKyAi"
    "IC8gIiArIHRvdGFsU2hvdHMgKyAiIOy0rOyYgSDsmYTro4wiOwogICAgICBhd2FpdCBzbGVlcCg3MDApOwogICAgfQoKICAgIHN0"
    "YXR1c0VsLmlubmVyVGV4dCA9ICLrqqjrk6Ag7LSs7JiB7J20IOyZhOujjOuQmOyXiOyKteuLiOuLpC4g6rKw6rO866W8IOu2iOuf"
    "rOyYpOuKlCDspJEuLi4iOwogICAgaWYgKHZpZGVvU3RyZWFtKSB7CiAgICAgIHZpZGVvU3RyZWFtLmdldFRyYWNrcygpLmZvckVh"
    "Y2goKHQpID0+IHQuc3RvcCgpKTsKICAgIH0KICAgIG5vdGlmeUhvc3QoeyBwaG90b3M6IGNhcHR1cmVkUGhvdG9zIH0pOwogIH0K"
    "CiAgLy8gY29tcG9uZW50IGxpZmVjeWNsZSBib290c3RyYXAKICBfc2VuZE1lc3NhZ2UoQ09NUE9ORU5UX1JFQURZLCB7IGFwaVZl"
    "cnNpb246IDEgfSk7CiAgd2luZG93LmFkZEV2ZW50TGlzdGVuZXIoImxvYWQiLCAoKSA9PiB7CiAgICBzZXRGcmFtZUhlaWdodChz"
    "dGFnZUhlaWdodCArIDIwKTsKICAgIGxheW91dFdpbmRvdygpOwogIH0pOwo8L3NjcmlwdD4KPC9ib2R5Pgo8L2h0bWw+"
)

_CAMERA_HTML = base64.b64decode(_CAMERA_HTML_B64).decode("utf-8")


@st.cache_resource
def _get_camera_component():
    tmp_dir = tempfile.mkdtemp(prefix="camera_component_")
    with open(os.path.join(tmp_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(_CAMERA_HTML)
    return components.declare_component("camera_capture", path=tmp_dir)


def camera_capture(aspect_ratio: float = 1.0, shots: int = 4, height: int = 680, key=None):
    component_func = _get_camera_component()
    return component_func(
        aspectRatio=aspect_ratio,
        shots=shots,
        height=height,
        key=key,
        default=None,
    )


# --------------------------------------------------------------------------
# Frame definitions
# Each frame image has 4 photo "slots". Coordinates were measured directly
# from the provided frame images (pixel boxes: x0, y0, x1, y1), listed in the
# order photos should be taken / placed (top to bottom).
# --------------------------------------------------------------------------
FRAMES = {
    "frame3": {
        "label": "하트 & 클로버 (블루)",
        "path": os.path.join(BASE_DIR, "assets", "frame3.jpg"),
        "slots": [
            (373, 74, 674, 436),
            (38, 250, 339, 612),
            (373, 451, 674, 813),
            (38, 627, 339, 988),
        ],
    },
    "frame2": {
        "label": "필름 스트립 (화이트)",
        "path": os.path.join(BASE_DIR, "assets", "frame2.jpg"),
        "slots": [
            (167, 79, 565, 378),
            (167, 416, 565, 715),
            (167, 754, 565, 1052),
            (167, 1091, 565, 1389),
        ],
    },
    "frame1": {
        "label": "필름 스트립 (블랙)",
        "path": os.path.join(BASE_DIR, "assets", "frame1.jpg"),
        "slots": [
            (246, 43, 514, 227),
            (246, 238, 514, 422),
            (246, 434, 514, 629),
            (246, 641, 514, 818),
        ],
    },
}

def _check_assets():
    missing = []
    for info in FRAMES.values():
        if not os.path.isfile(info["path"]):
            missing.append(info["path"])
    return missing


_missing_assets = _check_assets()
if _missing_assets:
    st.error(
        "다음 프레임 이미지 파일을 찾을 수 없습니다. GitHub 저장소에 `assets` 폴더와 "
        "이미지 3장이 `main.py`와 같은 위치에 올바른 이름으로 업로드되어 있는지 확인해주세요:\n\n"
        + "\n".join(f"- `{p}`" for p in _missing_assets)
        + "\n\n(저장소 구조가 `main.py` / `assets/frame1.jpg` / `assets/frame2.jpg` / "
        "`assets/frame3.jpg` 형태여야 합니다.)"
    )
    st.stop()

if "step" not in st.session_state:
    st.session_state.step = "select"
if "frame_key" not in st.session_state:
    st.session_state.frame_key = None
if "result_image" not in st.session_state:
    st.session_state.result_image = None


def slot_aspect_ratio(frame_key: str) -> float:
    x0, y0, x1, y1 = FRAMES[frame_key]["slots"][0]
    return (x1 - x0) / (y1 - y0)


def compose_final_image(frame_key: str, photo_data_urls):
    frame_info = FRAMES[frame_key]
    frame_img = Image.open(frame_info["path"]).convert("RGB")
    result = frame_img.copy()

    for (x0, y0, x1, y1), data_url in zip(frame_info["slots"], photo_data_urls):
        header, encoded = data_url.split(",", 1)
        photo_bytes = base64.b64decode(encoded)
        photo = Image.open(io.BytesIO(photo_bytes)).convert("RGB")

        target_w, target_h = x1 - x0, y1 - y0
        fitted = ImageOps.fit(photo, (target_w, target_h), Image.LANCZOS)
        result.paste(fitted, (x0, y0))

    return result


def reset_to_start():
    st.session_state.step = "select"
    st.session_state.frame_key = None
    st.session_state.result_image = None


# --------------------------------------------------------------------------
# STEP 1: select a frame
# --------------------------------------------------------------------------
def render_select_step():
    st.title("📸 포토부스")
    st.write("먼저 마음에 드는 프레임을 선택해주세요.")

    cols = st.columns(3)
    for col, key in zip(cols, FRAMES.keys()):
        info = FRAMES[key]
        with col:
            st.image(info["path"], use_container_width=True)
            selected = st.session_state.frame_key == key
            btn_label = "✅ 선택됨" if selected else "이 프레임 선택"
            if st.button(btn_label, key=f"choose_{key}", use_container_width=True):
                st.session_state.frame_key = key
                st.rerun()
            st.caption(info["label"])

    st.divider()
    disabled = st.session_state.frame_key is None
    if st.button("🎬 촬영 시작하기", type="primary", use_container_width=True, disabled=disabled):
        st.session_state.step = "shoot"
        st.rerun()

    if disabled:
        st.info("프레임을 하나 선택하면 시작 버튼이 활성화됩니다.")


# --------------------------------------------------------------------------
# STEP 2: shoot 4 photos via the camera component
# --------------------------------------------------------------------------
def render_shoot_step():
    frame_key = st.session_state.frame_key
    st.title("📷 촬영하기")
    st.write("카메라 화면 가운데 창에 맞춰 포즈를 잡고 '촬영 시작'을 눌러주세요. "
             "3-2-1 카운트다운 후 자동으로 4번 촬영됩니다.")

    aspect = slot_aspect_ratio(frame_key)
    result = camera_capture(aspect_ratio=aspect, shots=4, height=680, key=f"cam_{frame_key}")

    if result and result.get("photos") and len(result["photos"]) == 4:
        final_img = compose_final_image(frame_key, result["photos"])
        st.session_state.result_image = final_img
        st.session_state.step = "result"
        st.rerun()

    st.divider()
    if st.button("⬅️ 프레임 다시 선택하기"):
        reset_to_start()
        st.rerun()


# --------------------------------------------------------------------------
# STEP 3: show result, allow download or retake
# --------------------------------------------------------------------------
def render_result_step():
    st.title("🎉 완성!")
    st.write("촬영한 사진이 프레임에 맞춰 완성되었습니다.")

    final_img = st.session_state.result_image
    st.image(final_img, use_container_width=True)

    buf = io.BytesIO()
    final_img.save(buf, format="PNG")
    buf.seek(0)
    filename = f"photobooth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "💾 저장하기 (PNG)",
            data=buf,
            file_name=filename,
            mime="image/png",
            type="primary",
            use_container_width=True,
        )
    with col2:
        if st.button("🔄 다시 하기", use_container_width=True):
            reset_to_start()
            st.rerun()


# --------------------------------------------------------------------------
# router
# --------------------------------------------------------------------------
if st.session_state.step == "select":
    render_select_step()
elif st.session_state.step == "shoot":
    render_shoot_step()
elif st.session_state.step == "result":
    render_result_step()
