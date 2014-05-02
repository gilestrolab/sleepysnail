$( document ).ready(function() {
	$("ul.navbar-nav li").removeClass('active');
	var page = $(location).attr('href');
	console.log(page);
	//console.log($(location).attr('href'));
	console.log($('ul.navbar-nav li a[href$="'+page+'"]'));
	$('ul.navbar-nav li a[href$="'+page+'"]').parents().addClass('active');
	});
