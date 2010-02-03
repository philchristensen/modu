var task_ids = {}

function setProgress(progress_id, value, maxvalue){
	var progressField = $('#' + progress_id);
	var progressBar = progressField.children('.progress-bar');
	var progressText = progressField.children('.progress-text');
	
	if(value > 0 && value == maxvalue){
		progressBar.css('width', progressField.width() + "px");
		progressText.html('Complete!');
	}
	else if(value == 0){
		progressBar.css('width', 0);
		progressText.html('Waiting...');
	}
	else if(value == -1){
		progressText.html('Error!');
	}
	else{
		var percent = value / maxvalue;
		var client_width = progressField.width();
		var width = Math.round(percent * client_width) + "px";
		
		progressBar.css('width', width);
		progressText.html(Math.floor(percent * 100) + '%');
	}
}

function waitForCompletion(progress_id, callback_url, interval){
	var progressField = $('#' + progress_id);
	var progressText = progressField.children('.progress-text');
	
	progressText.html('0%');
	task_id = setInterval(checkProgress, interval, callback_url, progress_id);
	task_ids[progress_id] = task_id;
}

function checkProgress(callback_url, progress_id){
	jQuery.ajax({
		url: 		callback_url + '/' + progress_id,
		datatype:	'text',
		success:	function(data, textStatus){
						checkProgressCallback(data, textStatus, progress_id);
					},
		error:		function(request, textStatus, errorThrown){
						checkProgressErrback(request, textStatus, errorThrown, progress_id);
					}
	});
}

function checkProgressCallback(data, textStatus, progress_id){
	var stats = data.split('/');
	var value = parseInt(stats[0]);
	var maxvalue = parseInt(stats[1]);
	
	setProgress(progress_id, value, maxvalue);
	
	if(value > 0 && value == maxvalue){
		stopProgressBar(progress_id, false);
	}
}

function checkProgressErrback(request, textStatus, errorThrown, progress_id) {
	stopProgressBar(progress_id, true);
}

function stopProgressBar(progress_id, is_error){
	if(is_error){
		setProgress(progress_id, -1, 0);
	}
	
	if(task_ids[progress_id]){
		clearInterval(task_ids[progress_id]);
		delete task_ids[progress_id];
	}
}
