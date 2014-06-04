var prefixes = ["dag", "fig", "math"]

var media_map = {"raw":"1044213",
"concat": "1045563",
"rois": "1045435",
"undist": "1045433",
"daynight": "1045484",
"contours": "1041210"};

var media_url_template = ["http://wl.figshare.com/articles/", 
						  "/embed?show_title=0"];


$( document ).ready(function() {
	$("ul.navbar-nav li").removeClass('active');
	var page = $(location).attr('href');
	
	$('ul.navbar-nav li a[href$="'+page+'"]').parents().addClass('active');
	//resetDag("")
	});

var resetDag = function(tag){
	for(p in prefixes){
		$('.' + prefixes[p] + '_div .process').attr("class", "process active");
		}
	};



var updateDag = function(tag){
	
	suffix = tag.split("_")[1]
	for(p in prefixes){
		$('.' + prefixes[p] + '_div .process').attr("class", "process");
		id = '#' + prefixes[p] + '_' + suffix
		$(id).attr("class", "process active");
		//$(id).html($(id).html());
		if(prefixes[p] == "fig"){
			url = media_url_template[0]+ media_map[suffix]+media_url_template[1];
			$(id).find("iframe").attr("src", url);
			}
		}
	
	};

