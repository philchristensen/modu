submit_callbacks = []

function form_submit(){
	for(index in submit_callbacks){
		eval(submit_callbacks[index]);
	}
}

function add_submit_hook(hook){
	submit_callbacks.push(hook);
}