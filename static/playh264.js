const socketHostname = window.location.hostname;
const socketPort = window.location.port;
let ws_url = `http://${socketHostname}:${socketPort}`;
window.ws = io.connect(ws_url);

const player =window.video_player = new Player({
        useWorker: true,
        wbgl: 'auto',
        size: { width: 400, height: 400 },
        workerFile: "/static/Decoder.js",
        preserveDrawingBuffer: true});

function attach_canvas(canvas) {
    let playerElement = $('#container')
    playerElement.append(canvas)
    console.log("attach_canvas video")
    return canvas;
}



window.ws.on('connect', function () {
    console.log('Connected to server');
    attach_canvas(player.canvas)
});
window.ws.on('error', () => {
    console.log("Failed connect to device, maybe adb offline !!!");
});

window.ws.on('video_nal', function (message) {
    let unit8_data = new Uint8Array(message)
    let data_size = unit8_data.length
    console.log("video_nal data size = "+data_size)
    player.decode(unit8_data);
});

window.ws.onclose = () => {
    console.log('ws: Client disconnected')
}
