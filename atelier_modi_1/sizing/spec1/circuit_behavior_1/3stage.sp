.title Project: Three-STAGE OPAMP
.inc 'opamp.sp'
.inc 'param'

xac vin_ac vo_ac gnd opamp
vin vin_ac 0 ac=1

.OPTIONS INGOLD=0
.option post=2
.op

.ac dec 100 1 1g
.print vdb(vo_ac)
.print vp(vo_ac)
.meas ac gain find vdb(vo_ac) at=1
*.meas ac ugf_actual when vdb(vo_ac)=0
.meas ac ugf when vdb(vo_ac)=0
.meas ac phase FIND vp(vo_ac) at=ugf
.pz v(vo_ac) vin
*.meas ac phase max '180-sgn(vp(vo_ac))*vp(vo_ac)' from=1 to=ugf
*.meas ac phase max 'vp(vo_ac)/180' from=1 to=ugf
*.meas ac ugf=param('ugf_actual * 1e-6')
*.meas ac pm=param('phase + 180')

*.print ac Adm=par('20*log10(v(out)/v(vp))')
*.print ac Phase=par('vp(out)')

*.lib "./hspice/l0065ll_v1p5.lib" TT
.TEMP 27


.end
