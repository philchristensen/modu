function select_foreign_item(ac_cb_id){
	return function(li){
		document.getElementById(ac_cb_id).value = li.extra[0];
	};
}

function add_foreign_item(autocomplete_id, select_id){
	return function(li){
		foreign_select = document.getElementById(select_id);
		foreign_select.options[foreign_select.options.length] = new Option(li.innerHTML, li.extra[0]);
		
		autocomplete = document.getElementById(autocomplete_id);
		autocomplete.value = '';
	};
}