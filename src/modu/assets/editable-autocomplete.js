function select_item(ac_cb_id){
	return function(li){
		document.getElementById(ac_cb_id).value = li.extra[0];
	};
}

function select_item_handler(ac_cb_id){
	return function(data, value){
		document.getElementById(ac_cb_id).value = value[1]
	};
}

function add_foreign_item(form_name, field_name){
	return function(li){
		var value = li.extra[0];
		
		var foreign_select_id = field_name + '-foreign-select'
		var foreign_select = document.getElementById(foreign_select_id);
		foreign_select.options[foreign_select.options.length] = new Option(li.innerHTML, value);
		
		var hidden_value = document.createElement('input');
		hidden_value.setAttribute('type', 'hidden');
		hidden_value.setAttribute('name', form_name + '[' + field_name + ']');
		hidden_value.setAttribute('value', value);
		
		foreign_select.parentNode.insertBefore(hidden_value, foreign_select.nextSibling)
		
		var autocomplete_id = form_name + '-' + field_name + '-autocomplete'
		var autocomplete = document.getElementById(autocomplete_id);
		autocomplete.value = '';
		autocomplete.focus()
	};
}

