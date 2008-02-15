var task_ids = {}

function set_progress(progress_id, value, maxvalue){
	var progressField = $('#' + progress_id);
	var progressBar = progressField.children('.progress-bar');
	var progressText = progressField.children('.progress-text');
	
	if(value > 0 && value == maxvalue){
		progressBar.css('width', progressField.width() + "px");
		progressText.html('100%');
	}
	else if(value == 0){
		progressBar.css('width', 0);
		progressText.html('Waiting...');
	}
	else if(value == 'complete'){
		progressBar.css('width', progressField.width());
		progressText.html('Complete!');
	}
	else if(value == 'error'){
		progressText.html('Error!');
	}
	else{
		var percent = value / maxvalue;
		var client_width = progressField.width();
		var width = Math.round(percent * client_width) + "px";
		
		progressBar.css('width', width);
		progressText.html(Math.round(percent * 100) + '%');
	}
}

function waitForCompletion(progress_id, callback_url, interval){
	var progressField = $('#' + progress_id);
	var progressText = progressField.children('.progress-text');
	
	progressText.html('0%');
	task_id = setInterval(checkProgress, interval, callback_url, progress_id);
	task_ids[progress_id] = 'task-' + task_id;
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
	if(data == 'complete'){
		clearInterval(task_ids[progress_id])
		delete task_ids[progress_id];
		set_progress(progress_id, 'complete', 1);
		return;
	}
	
	var stats = data.split('/');
	var value = stats[0];
	var maxvalue = stats[1];
	
	if(value == 0){
		set_progress(progress_id, 0, 1);
	}
	else{
		set_progress(progress_id, value, maxvalue);
	}
}

function checkProgressErrback(request, textStatus, errorThrown, progress_id) {
	set_progress(progress_id, 'error', 0);
	if(task_ids[progress_id]){
		clearInterval(task_ids[progress_id])
		delete task_ids[progress_id];
	}
}
