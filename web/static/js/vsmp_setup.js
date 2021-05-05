function saveConfig(){
  // build the json post
  postData = {"mode": $('#config_mode').val(),
             "path": $('#config_path').val(),
             "update": $('#config_update').val(),
             "increment": parseInt($('#config_increment').val()),
             "start": parseInt($('#config_start').val()),
             "end": parseInt($('#config_end').val()) };

  // display represented as an array
  display = [];
  if($('#config_display_title').is(':checked'))
  {
    display.push('title');
  }

  if($('#config_display_timecode').is(':checked'))
  {
    display.push('timecode');
  }

  if($('#config_display_ip').is(':checked'))
  {
    display.push('ip');
  }

  postData.display = display;

  if($('#config_allow_seek').is(':checked'))
  {
    postData.allow_seek = true
  }
  else
  {
      postData.allow_seek = false
  }

  if($('#config_startup_screen').is(':checked'))
  {
    postData.startup_screen = true
  }
  else
  {
      postData.startup_screen = false
  }

  // post to api endpoint
  $.ajax({type: 'POST', contentType: 'application/json', url: '/api/configuration', data: JSON.stringify(postData), success: function(data, status, request){

    if(data.success)
    {
      showFlash(data.message, 'success')
    }
    else
    {
      showFlash(data.message, 'error');
    }
  }});

}
