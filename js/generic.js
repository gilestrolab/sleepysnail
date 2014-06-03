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
	for(p in prefixes){
		$('.' + prefixes[p] + '_div .process').attr("class", "process");
		id = '#' + prefixes[p] + '_' + suffix
		$(id).attr("class", "process active");
		}
	};

