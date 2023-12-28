// -------------------------------- Welding cam app management -------------------------------- 

// Pooling to get the cam state with get requests
var cam_weld_streaming = document.getElementById('cam-w-streaming');
var cam_weld_analy = document.getElementById('cam-w-analy');
var cam_weld_trig = document.getElementById('cam-w-trig');
var cam_weld_ok = document.getElementById('cam-w-ok');
var cam_weld_err = document.getElementById('cam-w-err');
var cam_weld_measure = document.getElementById('cam-w-measure');
var cam_weld_cod_err = document.getElementById('cam-w-cod-err');
var img_result_weld = document.getElementById('img-result-weld');

// Get the cam response from the server:  Update states, measure, error code and image
function get_cam_weld_response() {
  fetch('/states_welding')
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      // console.log(data);
      // data has 7 fields:trigger, connected, ok, distancia, error, error_code, imagen
      if (data.camera_response.trigger == true) {
        cam_weld_trig.style.backgroundColor = "green";
      }
      else {
        cam_weld_trig.style.backgroundColor = "white";
      }
      if (data.camera_response.connected == true) {
        cam_weld_analy.style.backgroundColor = "green";
      }
      else {
        cam_weld_analy.style.backgroundColor = "white";
      }      
      if (data.camera_response.ok == true) {
        cam_weld_ok.style.backgroundColor = "green";
      }
      else {
        cam_weld_ok.style.backgroundColor = "white";
      }
      if (data.camera_response.error == true) {
        cam_weld_err.style.backgroundColor = "red";
      }
      else {
        cam_weld_err.style.backgroundColor = "white";
      }
      cam_weld_measure.innerText = data.camera_response.distancia + " mm";
      cam_weld_cod_err.innerText = data.camera_response.error_code;
      if (data.camera_response.imagen != null) {
        img_result_weld.src = 'data:image/jpeg;base64,' + data.camera_response.imagen;
      }
      else {
        img_result_weld.src = '';
      }
    });
}

// execute each second
setInterval(get_cam_weld_response, 500);

// SocketIO streaming connection
const socket_weld = io.connect('http://' + document.domain + ':' + location.port);

socket_weld.on('connect', function() {
  console.log('Connected cam welding streaming socket');
});

socket_weld.on('disconnect', function() {
  console.log('Socket cam welding conecction lost');
});

socket_weld.on('video_frame', function(data) {
  // console.log('Received frame');
  document.getElementById('video-stream-weld').src = 'data:image/jpeg;base64,' + data.frame;
});

socket_weld.on('init', function(data) {
  // data has 2 field: streaming_state, presets; print it in the console  
  var table = document.getElementById('presets-items');
  table.innerHTML = '';
  
  for (var i = 0; i < data.presets.length; i++) {
    const row = document.createElement('tr');

    // Create a new div element with the preset ID and name
    const div = document.createElement('div');
    div.classList.add('d-flex', 'px-2', 'py-1');
    div.id = `preset-${i}`;
    div.innerText = data.presets[i];

    // Add a click event listener to the div element
    div.addEventListener('click', () => {
      //print the innner text of the div
      console.log(div.innerText);
      // Send the data to the server
      fetch('/goto_preset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: div.innerText
        })
      })
    });

    // Append the div element to the row element
    row.appendChild(div);

    // Append the row element to the table element
    table.appendChild(row);
  }
});


// ----------- Welding cam button management --------------------------------
const startWeldButton = document.getElementById('video-button-weld');
const shootWeldButton = document.getElementById('shoot-button-weld');

// Add a click event listener to the shot button and handle the response
shootWeldButton.addEventListener('click', () => {
  fetch('/shoot_welding', {
    method: 'POST',
  })
  .then(response => response.json())
  .then(data => console.log(data))
  .catch((error) => {
    console.error('Error:', error);
  });
});

// Add a click event listener to the start button read if 
startWeldButton.addEventListener('click', () => {
  fetch('/streaming_welding', {
    method: 'POST',
  })
  .then(response => response.json())
  .then(data => console.log(data))
  .catch((error) => {
    console.error('Error:', error);
  });
});

// ----------- Joystick
const up_button = document.getElementById('up-button');
const down_button = document.getElementById('down-button');
const left_button = document.getElementById('left-button');
const right_button = document.getElementById('right-button');

up_button.addEventListener('click', function() {
  fetch('/move_up')
    .then(function(response) {
      console.log('Up');
    });
});
down_button.addEventListener('click', function() {
  fetch('/move_down')
    .then(function(response) {
      console.log('Down');
    });
});
left_button.addEventListener('click', function() {
  fetch('/move_left')
    .then(function(response) {
      console.log('Left');
    });
});
right_button.addEventListener('click', function() {
  fetch('/move_right')
    .then(function(response) {
      console.log('Right');
    });
});


// -------------------------------- Cola cam app management --------------------------------
// Pooling to get the cam state with get requests
var cam_cola_streaming = document.getElementById('cam-c-streaming');
var cam_cola_analy = document.getElementById('cam-c-analy');
var cam_cola_trig = document.getElementById('cam-c-trig');
var cam_cola_ok = document.getElementById('cam-c-ok');
var cam_cola_err = document.getElementById('cam-c-err');
var cam_cola_measure = document.getElementById('cam-c-measure');
var cam_cola_cod_err = document.getElementById('cam-c-cod-err');
var img_result_cola = document.getElementById('img-result-cola');

// Get the cam response from the server:  Update states, measure, error code and image
function get_cam_cola_response() {
  fetch('/states_cola')
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      // console.log(data);
      // data has 7 fields:trigger, connected, ok, distancia, error, error_code, imagen
      if (data.camera_response.trigger == true) {
        cam_cola_trig.style.backgroundColor = "green";
      }
      else {
        cam_cola_trig.style.backgroundColor = "white";
      }
      if (data.camera_response.connected == true) {
        cam_cola_analy.style.backgroundColor = "green";
      }
      else {
        cam_cola_analy.style.backgroundColor = "white";
      }      
      if (data.camera_response.ok == true) {
        cam_cola_ok.style.backgroundColor = "green";
      }
      else {
        cam_cola_ok.style.backgroundColor = "white";
      }
      if (data.camera_response.error == true) {
        cam_cola_err.style.backgroundColor = "red";
      }
      else {
        cam_cola_err.style.backgroundColor = "white";
      }
      cam_cola_measure.innerText = data.camera_response.distancia + " mm";
      cam_cola_cod_err.innerText = data.camera_response.error_code;
      if (data.camera_response.imagen != null) {
        img_result_cola.src = 'data:image/jpeg;base64,' + data.camera_response.imagen;
      }
      else {
        img_result_cola.src = '';
      }
    });
}

// execute each second
setInterval(get_cam_cola_response, 500);

// SocketIO streaming connection
const socket_cola = io.connect('http://' + document.domain + ':' + location.port);

socket_cola.on('connect', function() {
  console.log('Connected cam cola streaming socket');
});

socket_cola.on('disconnect', function() {
  console.log('Socket cam cola conecction lost');
});

socket_cola.on('video_frame', function(data) {
  // console.log('Received frame');
  document.getElementById('video-stream-cola').src = 'data:image/jpeg;base64,' + data.frame;
});


// ----------- Cola cam button management --------------------------------
const startColaButton = document.getElementById('video-button-cola');
const shootColaButton = document.getElementById('shoot-button-cola');

// Add a click event listener to the shot button and handle the response
shootColaButton.addEventListener('click', () => {
  fetch('/shoot_cola', {
    method: 'POST',
  })
  .then(response => response.json())
  .then(data => console.log(data))
  .catch((error) => {
    console.error('Error:', error);
  });
});

// Add a click event listener to the start button read if
startColaButton.addEventListener('click', () => {
  fetch('/streaming_cola', {
    method: 'POST',
  })
  .then(response => response.json())
  .then(data => console.log(data))
  .catch((error) => {
    console.error('Error:', error);
  });
});