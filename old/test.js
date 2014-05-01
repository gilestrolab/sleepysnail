
function makeDate(){
  var today = new Date();
  var dd = today.getDate();
  var mm = today.getMonth()+1; //January is 0!
  var yyyy = today.getFullYear();

  if(dd<10)
      dd='0'+dd;
  if(mm<10)
      mm='0'+mm;
  today = yyyy + '-' + mm + '-' + dd;
  var elem = document.getElementById("date");
  elem.value = today;  
}

function makeCode () {	
  
	var title = document.getElementById("title");
	var date = document.getElementById("date");
	var number = document.getElementById("number");
  
	dict = {};
	dict.t = title.value;  
	dict.d = date.value;
	dict.n = number.value;
  
	var out = JSON.stringify(dict);
	qrcode.makeCode(out);
	
	setTimeout(drawInfo,500)
    
  
}
function drawInfo(){
	
	var canvas = document.getElementById("myCanvas");
  
	var context = canvas.getContext("2d");
	context.clearRect ( 0 , 0 , 1000 , 1000 );
	context.font = '25pt Calibri';
	var to_write =  + '\n' + dict.d + '\n'+ dict.n;
	context.textAlign="left";
	context.fillText(dict.t, 260, 50);
	context.fillText(dict.d, 260, 100);
	context.fillText("Arena #" + dict.n, 260, 150);
	context.drawImage(qr_img[0],0,0);
}
var dict;
var qrcode;
var qr_div;
var qr_img;

$( document ).ready(function() {
	qrcode= new QRCode("qrcode");
	qr_div= document.getElementById("qrcode");
	qr_img= qr_div.getElementsByTagName("img");
	
	makeDate();
	makeCode();
});
