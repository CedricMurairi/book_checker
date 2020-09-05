var menu_icon = document.getElementById('menu-icon');
var navbar = document.getElementById('navbar');
var close = document.getElementById('close');

menu_icon.onclick = function(){
	navbar.classList.toggle('show');
	menu_icon.style.display = 'none';
	close.style.display = 'block';
}

close.onclick = function() {
	navbar.classList.toggle('show');
	menu_icon.style.display = 'flex';
	close.style.display = 'none';
}