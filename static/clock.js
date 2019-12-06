var tday=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  var tmonth=["Jan","Feb","Mar","Apr","May","June","July","Aug","Sep","Oct","Nov","Dec"];

  function GetClock(){
    var d=new Date();
    var nday=d.getDay(),nmonth=d.getMonth(),ndate=d.getDate(),nyear=d.getFullYear();
    var nhour=d.getHours(),nmin=d.getMinutes(),nsec=d.getSeconds(),ap;

    if(nhour==0){ap=" AM";nhour=12;}
      else if(nhour<12){ap=" AM";}
      else if(nhour==12){ap=" PM";}
      else if(nhour>12){ap=" PM";nhour-=12;}

    if(nmin<=9) nmin="0"+nmin;
    if(nsec<=9) nsec="0"+nsec;

    var clocktext=""+tday[nday]+", "+tmonth[nmonth]+" "+ndate+", "+nyear+" "+"\n"+nhour+":"+nmin+":"+nsec+ap+"";
    $('#clockbox').html(`
      <div class="date">
        ${tday[nday]}, ${tmonth[nmonth]} ${ndate}, ${nyear}
      </div>
      <div class="time">
        ${nhour}:${nmin}:${nsec}${ap}
      </div>
    `);
  }

  GetClock();
  setInterval(GetClock,1000);

  