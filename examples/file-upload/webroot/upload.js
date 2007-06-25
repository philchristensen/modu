var task_id = undefined;

function waitForCompletion(file_element){
	var progressText = $('progress-text');
	progressText.innerHTML = '0%';
	task_id = setInterval(checkTotal, 1000, file_element.value);
}

function checkTotal(filename){
	filename = filename.split('/').pop();
	var ajax = new Ajax.Request('status/' + filename, {method:'get', onSuccess:checkTotalCallback, onFailure:checkTotalErrback});
}

function checkTotalCallback(response){
	var progressField = $('progress-field');
	var progressBar = $('progress-bar');
	var progressText = $('progress-text');
	var stats = response.responseText.split('/');
	if(response.responseText == 'complete'){
		clearInterval(task_id)
		task_id = undefined;
		progressBar.style.width = progressField.clientWidth + "px";
		progressText.innerHTML = '100%';
	}
	else if(stats[0] == 0){
		progressText.innerHTML = 'Waiting...';
	}
	else{
		var percent = stats[0] / stats[1];
		progressBar.style.width = Math.round(percent * progressField.clientWidth) + "px";
		progressText.innerHTML = Math.round(percent * 100) + '%';
	}
}

function checkTotalErrback(response) {
	var progressField = $('progress-text');
	progressField.innerHTML = 'Error ' + response.status + ' -- ' + response.statusText;
	if(task_id){
		clearInterval(task_id)
		task_id = undefined;
	}
}
