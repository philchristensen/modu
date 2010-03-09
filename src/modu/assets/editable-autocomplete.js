function select_item(ac_cb_id){
	return function(li){
		document.getElementById(ac_cb_id).value = li.extra[0];
	};
}

function select_item_handler(ac_cb_id){
	return function(data, value){
		document.getElementById(ac_cb_id).value = value[1];
	};
}

// function add_foreign_item(form_name, field_name){
// 	return function(li){
		// var value = li.extra[0];
function add_foreign_item(form_name, field_name){
	return function(data, value){
		var text = value[0];
		var value = value[1];
		
		var foreign_select_id = field_name + '-foreign-select'
		var foreign_select = $('#' + foreign_select_id);
		foreign_select.append($('<option value="' + value + '">' + text + '</option>'));
		
		var hidden_value = $('<input type="hidden" name="' + form_name + '[' + field_name + ']" value="' + value + '" />');
		
		foreign_select.after(hidden_value);
		
		var autocomplete_id = form_name + '-' + field_name + '-autocomplete';
		var autocomplete = $('#' + autocomplete_id);
		autocomplete.val('');
		autocomplete.focus()
	};
}

