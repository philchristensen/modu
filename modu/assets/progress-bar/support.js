function set_progress(bar_id, value, maxvalue){
	var progressField = $('#' + bar_id);
	var progressBar = progressField.children('.progress-bar');
	var progressText = progressField.children('.progress-text');
	
	if(value > 0 && value == maxvalue){
		progressBar.css('width', progressField.width() + "px");
		progressText.html('100%');
	}
	else if(value == 0){
		progressText.html('Waiting...');
	}
	else{
		var percent = value / maxvalue;
		var client_width = progressField.width();
		var width = Math.round(percent * client_width) + "px";
		
		progressBar.css('width', width);
		progressText.html(Math.round(percent * 100) + '%');
	}
}