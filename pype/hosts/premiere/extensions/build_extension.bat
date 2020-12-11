@echo off
rem You need https://github.com/Adobe-CEP/CEP-Resources/raw/master/ZXPSignCMD/4.1.1/win64/ZXPSignCmd.exe

rem You need https://partners.adobe.com/exchangeprogram/creativecloud/support/exman-com-line-tool.html

rem !!! make sure you run windows power shell as admin

set pwd="12PPROext581"

echo ">>> creating certificate ..."
%YOWZA_PIPE_PATH%/utils/ZXPSignCmd -selfSignedCert CZ Prague OrbiTools "Signing robot" %pwd% certificate.p12
echo ">>> building com.pype"
%YOWZA_PIPE_PATH%/utils/ZXPSignCmd -sign com.pype/ extension.zxp certificate.p12 %pwd%
echo ">>> building com.pype.rename"
%YOWZA_PIPE_PATH%/utils/ZXPSignCmd -sign com.pype.rename/ pype_rename.zxp certificate.p12 %pwd%

echo ">>> installing com.pype"
%YOWZA_PIPE_PATH%/utils/ExManCmd_Win/ExManCmd.exe /install extension.zxp
echo ">>> installing com.pype.rename"
%YOWZA_PIPE_PATH%/utils/ExManCmd_Win/ExManCmd.exe /install pype_rename.zxp

