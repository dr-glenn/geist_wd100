<!DOCTYPE html>
<html>
<head>
<title>OOS Geist Watchdog</title>
<style>
table, th, td {
    border: 1px solid black;
}
</style>
</head>
<body>
<h1>OOS Environment</h1>
<p>
<?php
$fp = fopen("/home/pi/Projects/geist_wd100/geist_data.log", "r");
fseek($fp, -1, SEEK_END); 
$pos = ftell($fp);
$C = fgetc($fp);
//printf("pos start=%u<br>",$pos);
$LastLine = "";
// file might have trailing newlines, so skip those
while ($C === "\n" || $C === "\r") {
    fseek($fp, $pos--, SEEK_END);
    $C = fgetc($fp);
}
$LastLine = $C.$LastLine;	// valid $C, prepend to LastLine
// Loop backward until "\n" is found.
while((($C = fgetc($fp)) != "\n") && ($pos > 0)) {
    $LastLine = $C.$LastLine;
    fseek($fp, $pos--);
}
//printf("pos end=%u<br>",$pos);
//printf("str len=%u<br>",strlen($LastLine));
//printf("Most recent: %s",$LastLine);

// TODO: figure out how to scanf in chunks so that I don't have to repeat the format string.
//sscanf($LastLine, "INFO : %[^ ] %[^,],I:%[^,],V:%[^,],%f,V:%[^,],%f,V:%[^,],%f,%[^\n]",$date,$time,$instr1,$vtype1,$v1,$vtype2,$v2,$vtype3,$v3,$leftover);
//printf("<br>date=%s, time=%s, instr=%s, %s=%.1f, %s=%.1f, %s=%.1f, leftover=%s", $date,$time,$instr1,$vtype1,$v1,$vtype2,$v2,$vtype3,$v3,$leftover);

sscanf($LastLine, "INFO : %[^ ] %[^,]%[^\n]",$date,$time,$leftover);
printf("<br><table><tr><td colspan='2' style='text-align:center;'>Date=%s, Time=%s</td></tr>", $date, $time);
//printf("<br><table><tr><td colspan=2 >Date=%s, Time=%s</td></tr>", $date, $time);
printf("<tr><th>Instrument</th><th>Enviroment</th></tr>");
// don't know how much string remains, but if small amount, then not valid
$cnt = 0;
while (strlen($leftover) > 8 && $cnt < 10) {
    $more = "";
    $ret = sscanf($leftover, ",I:%[^,],V:%[^,],%f,V:%[^,],%f,V:%[^,],%f%[^\n]",$instr1,$vtype1,$v1,$vtype2,$v2,$vtype3,$v3,$more);
    //printf("<br>ret=%d",$ret);
    //printf("<br>more=%s",$more);
    $leftover = $more;
    //printf("<br>leftover=%s",$leftover);
    //printf("<br>instr=%s, %s=%.1f, %s=%.1f, %s=%.1f", $instr1,$vtype1,$v1,$vtype2,$v2,$vtype3,$v3);
    printf("<tr><td>%s</td><td>%s=%.1f, %s=%.1f, %s=%.1f</td></tr>", $instr1,$vtype1,$v1,$vtype2,$v2,$vtype3,$v3);
    $cnt++;
    if ($ret == -1) break;
}
printf("</table>");
?>
</p>
</body>
</html>
