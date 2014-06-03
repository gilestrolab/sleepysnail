prefixes = ["dag", "fig", "math"]

$( document ).ready(function() {
	$("ul.navbar-nav li").removeClass('active');
	var page = $(location).attr('href');
	console.log(page);
	//console.log($(location).attr('href'));
	console.log($('ul.navbar-nav li a[href$="'+page+'"]'));
	$('ul.navbar-nav li a[href$="'+page+'"]').parents().addClass('active');
	});

var updateDag = function(tag){
	
	suffix = tag.split("_")[1]
	console.log(prefixes)
	console.log(suffix)
	for(p in prefixes){
		$('.' + prefixes[p] + '_div .process').attr("class", "process");
		id = '#' + prefixes[p] + '_' + suffix
		console.log(id)
		$(id).attr("class", "process active");
		}
	};

