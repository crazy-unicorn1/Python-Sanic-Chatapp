var html = '<style>@media screen and (max-width: 800px){  #chatMainBox{width: 95% !important;}}</style><div id="chatMainBox" style="position: fixed; right: 0rem; bottom: 10px; overflow: hidden; box-sizing: border-box; z-index: 99999999999999999999; width: 400px; height: 80vh; border-radius: 5px;">\n' +
    '<iframe src="https://{#domain#}/chat/{#site_code#}/winChat.html" frameborder="0" style="position: relative; overflow: hidden; box-sizing: border-box; z-index: 99999999999999999999; width: 100%; height: 100%;"></iframe>\n' +
    '</div>'
var bodyElement = document.body;
bodyElement.insertAdjacentHTML("beforeend", html);
