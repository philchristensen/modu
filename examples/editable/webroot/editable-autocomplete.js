function select_foreign_item(ac_cb_id){
	return function(li){
		document.getElementById(ac_cb_id).value = li.extra[0];
	};
}

function select_all_foreign_items(select_id){
	foreign_select = document.getElementById(select_id);
	for(index in foreign_select.options){
		foreign_select.options[index].selected = true;
	}
}

function add_foreign_item(autocomplete_id, select_id){
	return function(li){
		foreign_select = document.getElementById(select_id);
		foreign_select.options[foreign_select.options.length] = new Option(li.innerHTML, li.extra[0]);
		
		autocomplete = document.getElementById(autocomplete_id);
		autocomplete.value = '';
		autocomplete.focus()
	};
}

