function toggleFileBrowser(){
  if($('#file_browser').is(':visible'))
  {
    $('#file_browser').hide();

    $('#file_browse_button').html('Browse').removeClass('btn-danger');
  }
  else
  {
    $('#file_browser').show();

    $('#file_browse_button').html('Close').addClass('btn-danger');
  }
}

function selectPath(path){

  // use passed in path if file mode, or current dir if directory mode
  if($('#config_mode').val() == 'dir')
  {
    path =  $('#file_path').html();
  }

  // set path in form input
  $('#config_path').val(path);

  // close the file browser
  toggleFileBrowser();
}

function toggleDirSelect(){
  $('#directory_select_button').toggle();

  if($('#file_browser').is(':visible')){
    // if currently browsing, refresh the file list
    loadFiles($('#file_path').html());
  }
}

// creates an onClick method based on a file path and name, optionally can change javascript function
function makePathLink(path, name, funcName = 'loadFiles'){
  return '<a href="#" onClick="return ' + funcName + '(\'' + path + '\')">' + name + '</a><br />';
}

function loadFiles(path){

  // send request to load file listings
  $.ajax({type: 'GET', contentType: 'application/json', url: '/api/browse_files/' + path, success: function(data, status, request){

    if(data.success)
    {

      // set the current full path
      $('#file_path').html(data.path)

      fileList = "";  // string with html to display contents of directory

      //create the UP Level icon, if not at root
      if(data.path != '/'){
        splitPath = data.path.split('/');
        splitPath.pop();

        fileList = makePathLink(splitPath.join('/'), '<i class="bi bi-arrow-90deg-up"></i> ..');
      }

      //build the html list
      for(i = 0; i < data.dirs.length; i++)
      {
        fileList = fileList + makePathLink(data.path + '/' + data.dirs[i], data.dirs[i]);
      }

      //build the html list
      for(i = 0; i < data.files.length; i++)
      {
        if($('#config_mode').val() == 'file')
        {
          fileList = fileList + makePathLink(data.path + '/' + data.files[i], data.files[i], 'selectPath');
        }
        else
        {
          fileList = fileList + data.files[i] + '<br />';
        }
      }

      $('#file_list').html(fileList);
    }
  }});

  return false;
}
