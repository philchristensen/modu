function get_ac_callback(ac_cb_id){
	return function(li){
		document.getElementById(ac_cb_id).value = li.extra[0];
	};
}