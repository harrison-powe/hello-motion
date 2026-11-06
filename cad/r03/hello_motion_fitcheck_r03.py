r"""Hello-Motion r03. PETG static fit check only. World dimensions in mm.
Run with CadQuery 2.7: python hello_motion_fitcheck_r03.py --out new_folder --references vendor_folder
The optional vendor folder must contain EG17-G5.STEP, MJ5208.step and moteus_devkit_bracket.step.
"""
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from collections import Counter
import argparse, hashlib, json, math, platform, struct
import cadquery as cq

@dataclass(frozen=True)
class P:
    rotor_x: float = 2.56
    axis_z: float = 49
    face_gap: float = 6
    plate_width: float = 60
    plate_height: float = 60
    plate_thickness: float = 6
    bore_d: float = 30
    flange_pitch: float = 31
    flange_hole_d: float = 3.7
    rotor_d: float = 63
    motor_body_length: float = 25
    rotor_radial_margin: float = 1
    rotor_axial_clearance: float = 1
    nut_af: float = 5.42
    nut_thickness: float = 2.3
    clearance_per_flat: float = 0.15
    screw_length: float = 10
    nut_pocket_depth: float = 3
    m3_head_envelope_d: float = 6
    m3_head_stack_max: float = 2.5
    driver_stem_d: float = 4
    base_x: float = -16.44
    base_y: float = -42
    base_length: float = 44
    base_width: float = 84
    base_thickness: float = 6
    leg_length: float = 16
    leg_width: float = 12
    leg_height: float = 13
    leg_x: float = -2.44
    gusset_run: float = 9
    base_hole_d: float = 6.6
    # Original rear X=-8.44 is under a motor cheek. New candidate centers:
    gb_hole_x1: float = 0
    gb_hole_x2: float = 19.56
    gb_hole_y: float = 36
    base_head_d: float = 10
    base_head_height: float = 6
    base_tool_d: float = 10.5
    base_separation: float = 0.75
    stand_length: float = 90
    stand_width: float = 110
    stand_thickness: float = 8
    cheek_x: float = -22.24
    cheek_depth: float = 14
    cheek_width: float = 12
    cheek_height: float = 57
    cheek_y_center: float = 37
    bracket_z_lower: float = 35
    bracket_z_upper: float = 53
    bracket_hole_d: float = 3.3
    stand_gusset_width: float = 5
    stand_gusset_end_x: float = 12
    stand_hole_x: float = 35
    stand_hole_y: float = 49
    hub_flange_d: float = 28
    hub_flange_length: float = 4
    hub_neck_d: float = 18
    hub_neck_length: float = 12
    hub_stub_d: float = 5
    hub_total_length: float = 30.5
    hub_pcd: float = 17
    hub_hole_d: float = 3.3
    hub_access_d: float = 7
    hub_screw_seat: float = 1.5
    shaft_pocket_d: float = 5.4
    shaft_pocket_depth: float = 2.3
    motor_shaft_d: float = 5
    motor_shaft_projection: float = 2
    gearbox_mouth_d: float = 22
    gearbox_bore_d: float = 5
    bore_start_from_face: float = 18.5
    bore_length: float = 7
    target_engagement: float = 6
    gearbox_frame: float = 42
    gearbox_body_length: float = 55
    gearbox_total_extent: float = 77
    mesh_linear: float = 0.03
    mesh_angular: float = 0.1


def need(ok,msg):
    if not ok: raise ValueError(msg)
def box(x,y,z,dx,dy,dz):
    return cq.Solid.makeBox(dx,dy,dz,cq.Vector(x,y,z))
def cyl(x,y,z,r,length,axis=(1,0,0)):
    return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(*axis))
def triangle_xz(y,width,points):
    v=[cq.Vector(x,y,z) for x,z in points]
    return cq.Solid.extrudeLinear(cq.Wire.makePolygon(v+[v[0]]),[],cq.Vector(0,width,0))
def volume_common(a,b): return a.intersect(b).Volume()
def clear(a,b,label,checks):
    v=volume_common(a,b); need(v<1e-6,label+f': overlap {v} mm3'); checks[label]=v

def hex_prism(x,y,z,af,length,angle=0):
    radius=af/math.sqrt(3)
    vertices=[cq.Vector(x,y+radius*math.cos(math.radians(angle+i*60)),z+radius*math.sin(math.radians(angle+i*60))) for i in range(6)]
    return cq.Solid.extrudeLinear(cq.Wire.makePolygon(vertices+[vertices[0]]),[],cq.Vector(length,0,0))

def build(p):
    g=p.rotor_x+p.face_gap; front=g-p.plate_thickness
    bottom=p.axis_z-p.plate_height/2
    need(abs(bottom-p.base_thickness-p.leg_height)<1e-8,'Legs must meet plate underside')
    need(p.face_gap==6,'This candidate preserves the specified 6 mm gap')
    need(p.hub_pcd==17,'This candidate is specifically the 17 mm output pattern')
    need(p.bore_d>p.hub_flange_d,'Opening must clear hub flange')
    relief_end=p.rotor_x+p.rotor_axial_clearance
    relief_depth=relief_end-front
    need(0<relief_depth<p.plate_thickness,'Invalid rotor relief depth')
    seat=relief_end+p.nut_pocket_depth
    need(g-seat>=1.5,'Faceplate screw seat too thin even for this fit-check candidate')
    need(p.nut_thickness<p.nut_pocket_depth,'Nut requires positive recess')
    need(p.hub_screw_seat+p.m3_head_stack_max<=p.hub_flange_length,'Hub head extends beyond flange')
    need(p.hub_access_d>p.m3_head_envelope_d and p.hub_access_d>p.driver_stem_d,'Hub channel too small')
    need(p.shaft_pocket_d>p.motor_shaft_d and p.shaft_pocket_depth>p.motor_shaft_projection,'Motor shaft pocket too small')
    need(p.hub_pcd/2-p.hub_access_d/2>p.shaft_pocket_d/2,'Hub channels meet central pocket')
    need(p.hub_pcd/2+p.hub_access_d/2<p.hub_flange_d/2,'Hub channels exit flange outer edge')
    need(math.sqrt(2)*(p.flange_pitch/2)>p.bore_d/2+(p.nut_af+2*p.clearance_per_flat)/math.sqrt(3),'Faceplate pockets meet center opening')
    flange_centers=[(y*p.flange_pitch/2,p.axis_z+z*p.flange_pitch/2) for y in (-1,1) for z in (-1,1)]
    face=box(front,-p.plate_width/2,bottom,p.plate_thickness,p.plate_width,p.plate_height)
    face=face.cut(cyl(front-1,0,p.axis_z,p.bore_d/2,p.plate_thickness+2))
    face=face.cut(cyl(front-1,0,p.axis_z,p.rotor_d/2+p.rotor_radial_margin,relief_depth+1))
    for y,z in flange_centers:
        face=face.cut(cyl(front-1,y,z,p.flange_hole_d/2,p.plate_thickness+2))
        face=face.cut(hex_prism(front-1,y,z,p.nut_af+2*p.clearance_per_flat,seat-front+1))
    face=face.clean()
    base=box(p.base_x,p.base_y,0,p.base_length,p.base_width,p.base_thickness)
    gb_holes=[(x,y) for x in (p.gb_hole_x1,p.gb_hole_x2) for y in (-p.gb_hole_y,p.gb_hole_y)]
    support=base.fuse(face)
    for y in (-p.plate_width/2,p.plate_width/2-p.leg_width):
        support=support.fuse(box(p.leg_x,y,p.base_thickness,p.leg_length,p.leg_width,p.leg_height))
        support=support.fuse(triangle_xz(y,p.leg_width,[(front-p.gusset_run,p.base_thickness),(front,p.base_thickness),(front,bottom)]))
        support=support.fuse(triangle_xz(y,p.leg_width,[(g,p.base_thickness),(g+p.gusset_run,p.base_thickness),(g,bottom)]))
    for x,y in gb_holes:
        need(p.base_x+p.base_hole_d/2<x<p.base_x+p.base_length-p.base_hole_d/2,'Base hole outside base')
        need(p.base_y+p.base_hole_d/2<y<p.base_y+p.base_width-p.base_hole_d/2,'Base hole outside base')
        support=support.cut(cyl(x,y,-1,p.base_hole_d/2,p.base_thickness+2,(0,0,1)))
    support=support.clean()
    # Open-front U base. It allows an axial insertion path, unlike a closed window.
    stand=box(-p.stand_length/2,-p.stand_width/2,0,p.stand_length,p.stand_width,p.stand_thickness)
    cut_x=p.base_x-p.base_separation
    stand=stand.cut(box(cut_x,p.base_y-p.base_separation,-1,p.stand_length/2-cut_x+1,p.base_width+2*p.base_separation,p.stand_thickness+2))
    for sign in (-1,1):
        yc=sign*p.cheek_y_center
        stand=stand.fuse(box(p.cheek_x,yc-p.cheek_width/2,p.stand_thickness,p.cheek_depth,p.cheek_width,p.cheek_height))
        # External ribs overlap the cheek by 0.5 mm; keep them outside reducer base.
        gy=p.cheek_y_center+p.cheek_width/2-0.5
        if sign<0: gy=-gy-p.stand_gusset_width
        stand=stand.fuse(triangle_xz(gy,p.stand_gusset_width,[(p.cheek_x,p.stand_thickness),(p.stand_gusset_end_x,p.stand_thickness),(p.cheek_x,p.bracket_z_upper+1)]))
    bracket_centers=[(y,z) for y in (-p.cheek_y_center,p.cheek_y_center) for z in (p.bracket_z_lower,p.bracket_z_upper)]
    for y,z in bracket_centers:
        stand=stand.cut(cyl(p.cheek_x-1,y,z,p.bracket_hole_d/2,p.cheek_depth+2))
    # The original cheeks begin at Y=31: relieve against an inflated Ø63 motor.
    motor_clear=cyl(p.rotor_x-p.motor_body_length-1,0,p.axis_z,p.rotor_d/2+p.rotor_radial_margin,p.motor_body_length+1+p.rotor_axial_clearance)
    stand=stand.cut(motor_clear)
    stand_holes=[(x,y) for x in (-p.stand_hole_x,p.stand_hole_x) for y in (-p.stand_hole_y,p.stand_hole_y)]
    for x,y in stand_holes: stand=stand.cut(cyl(x,y,-1,p.base_hole_d/2,p.stand_thickness+2,(0,0,1)))
    stand=stand.cut(box(-21,-15,6.5,8,30,p.stand_thickness-6.5+0.01)).clean()
    hub=cyl(p.rotor_x,0,p.axis_z,p.hub_flange_d/2,p.hub_flange_length).fuse(cyl(p.rotor_x+p.hub_flange_length,0,p.axis_z,p.hub_neck_d/2,p.hub_neck_length)).fuse(cyl(p.rotor_x,0,p.axis_z,p.hub_stub_d/2,p.hub_total_length))
    # Same native-to-world mapping as source: native (x,y,z) -> world(z-22.24,x,y+49).
    hub_centers=[(p.hub_pcd/2*math.cos(math.radians(a)),p.axis_z+p.hub_pcd/2*math.sin(math.radians(a))) for a in (180,60,-60)]
    for y,z in hub_centers:
        hub=hub.cut(cyl(p.rotor_x-1,y,z,p.hub_hole_d/2,p.hub_total_length+2))
        hub=hub.cut(cyl(p.rotor_x+p.hub_screw_seat,y,z,p.hub_access_d/2,p.hub_total_length))
    hub=hub.cut(cyl(p.rotor_x-1,0,p.axis_z,p.shaft_pocket_d/2,p.shaft_pocket_depth+1)).clean()
    return {'faceplate':face,'gearbox_support':support,'actuator_stand':stand,'hub_COMPANION_REQUIRED':hub}, {'flange':flange_centers,'hub':hub_centers,'bracket':bracket_centers,'gearbox_base':gb_holes,'stand_base':stand_holes}


def verify(p,parts,centers):
    checks={}; f=parts['faceplate']; s=parts['gearbox_support']; a=parts['actuator_stand']; h=parts['hub_COMPANION_REQUIRED']
    g=p.rotor_x+p.face_gap; front=g-p.plate_thickness; seat=p.rotor_x+p.rotor_axial_clearance+p.nut_pocket_depth
    for name,shape in parts.items(): need(shape.isValid() and len(shape.Solids())==1,name+' must be one valid solid')
    clear(a,s,'stand_vs_gearbox_support',checks)
    clear(h,s,'hub_vs_gearbox_support',checks)
    clear(h,a,'hub_vs_stand',checks)
    motor=cyl(p.rotor_x-p.motor_body_length,0,p.axis_z,p.rotor_d/2,p.motor_body_length)
    shaft=cyl(p.rotor_x,0,p.axis_z,p.motor_shaft_d/2,p.motor_shaft_projection)
    for name,shape in [('stand',a),('gearbox_support',s)]:
        clear(shape,motor,name+'_vs_motor_body_envelope',checks)
        need(shape.distance(motor)>=p.rotor_axial_clearance-1e-6,name+' lacks specified motor clearance')
    clear(h,shaft,'hub_vs_projecting_motor_shaft',checks)
    swept=cyl(p.rotor_x,0,p.axis_z,p.hub_flange_d/2,p.hub_flange_length).fuse(cyl(p.rotor_x+p.hub_flange_length,0,p.axis_z,p.hub_neck_d/2,p.hub_neck_length)).fuse(cyl(p.rotor_x,0,p.axis_z,p.hub_stub_d/2,p.hub_total_length))
    clear(s,swept,'support_vs_full_rotating_hub_envelope',checks)
    clear(a,swept,'stand_vs_full_rotating_hub_envelope',checks)
    mouth=box(g,-p.gearbox_frame/2,p.axis_z-p.gearbox_frame/2,1,p.gearbox_frame,p.gearbox_frame).cut(cyl(g-1,0,p.axis_z,p.gearbox_mouth_d/2,3))
    clear(swept,mouth,'hub_sweep_vs_22mm_mouth_proxy',checks)
    for y,z in centers['flange']:
        for name,shape in [('face',f),('support',s)]: clear(shape,cyl(front-1,y,z,p.flange_hole_d/2-.01,p.plate_thickness+2),name+f'_flange_hole_{y}_{z}',checks)
        nut=hex_prism(seat-p.nut_thickness,y,z,p.nut_af,p.nut_thickness)
        for part_name,part in [('face',f),('support',s)]:
            clear(part,nut,f'{part_name}_seated_nut_{y}_{z}',checks)
            clear(part,hex_prism(front-5,y,z,p.nut_af,seat-front+5),f'{part_name}_nut_insertion_{y}_{z}',checks)
            need(volume_common(part,hex_prism(seat-p.nut_thickness,y,z,p.nut_af,p.nut_thickness,30))>0.01,'Nut can spin freely')
        tip=g+5-p.screw_length
        shank=cyl(tip,y,z,1.5,p.screw_length)
        clear(s,shank,f'clearance_shank_{y}_{z}',checks)
        clear(motor,shank,f'screw_tip_vs_rotor_{y}_{z}',checks)
        need(tip<=seat-p.nut_thickness and tip>p.rotor_x,'Check screw reach and rotor clearance')
    for y,z in centers['hub']:
        clear(h,cyl(p.rotor_x-1,y,z,p.hub_hole_d/2-.01,p.hub_screw_seat+1),f'hub_hole_{y}_{z}',checks)
        head=cyl(p.rotor_x+p.hub_screw_seat,y,z,p.m3_head_envelope_d/2,p.m3_head_stack_max)
        clear(h,head,f'hub_head_{y}_{z}',checks)
        clear(h,cyl(p.rotor_x+p.hub_screw_seat,y,z,p.driver_stem_d/2,45),f'hub_driver_gearbox_removed_{y}_{z}',checks)
        clear(mouth,head,f'hub_head_vs_mouth_{y}_{z}',checks)
    for y,z in centers['bracket']:
        clear(a,cyl(p.cheek_x-1,y,z,p.bracket_hole_d/2-.01,p.cheek_depth+2),f'bracket_hole_{y}_{z}',checks)
        access=cyl(p.cheek_x+p.cheek_depth,y,z,4,60)
        clear(a,access,f'bracket_front_access_{y}_{z}',checks)
        clear(s,access,f'bracket_access_vs_support_{y}_{z}',checks)
    for group,shape,thick in [('gearbox_base',s,p.base_thickness),('stand_base',a,p.stand_thickness)]:
        for x,y in centers[group]:
            clear(shape,cyl(x,y,-1,p.base_hole_d/2-.01,thick+2,(0,0,1)),f'{group}_through_{x}_{y}',checks)
            head=cyl(x,y,thick,p.base_head_d/2,p.base_head_height,(0,0,1))
            clear(s,head,f'{group}_head_vs_support_{x}_{y}',checks)
            clear(a,head,f'{group}_head_vs_stand_{x}_{y}',checks)
            tool=cyl(x,y,thick+.001,p.base_tool_d/2,90,(0,0,1))
            clear(s,tool,f'{group}_tool_vs_support_{x}_{y}',checks)
            clear(a,tool,f'{group}_tool_vs_stand_{x}_{y}',checks)
    # Exact conservative bounds on continuous +60 mm axial support travel.
    base_sweep=box(p.base_x,p.base_y,0,p.base_length+60,p.base_width,p.base_thickness)
    upper_min=min(p.leg_x,front-p.gusset_run)
    upper_max=max(p.leg_x+p.leg_length,g+p.gusset_run)
    upper_sweep=box(upper_min,-p.plate_width/2,p.base_thickness,upper_max-upper_min+60,p.plate_width,p.axis_z+p.plate_height/2-p.base_thickness)
    clear(a,base_sweep,'continuous_insertion_base_bounding_sweep',checks)
    clear(a,upper_sweep,'continuous_insertion_upper_bounding_sweep',checks)
    # Actual solids also checked at explicit offsets as a diagnostic.

    for dx in (0,1,3,6,12,24,40,60): clear(a,s.translate((dx,0,0)),f'support_insertion_sample_x{dx}',checks)
    start=g+p.bore_start_from_face; end=start+p.bore_length; tip=p.rotor_x+p.hub_total_length
    overlap=min(tip,end)-max(start,p.rotor_x+p.hub_flange_length+p.hub_neck_length)
    need(abs(overlap-p.target_engagement)<1e-8,'Engagement changed')
    need(end-tip>0,'Stub bottoms in nominal bore')
    return {'checks_overlap_mm3':checks,'datums_mm':{'rotor_face_x':p.rotor_x,'gearbox_face_x':g,'bore_start_x':start,'bore_end_x':end,'stub_tip_x':tip,'engagement':overlap,'tip_clearance':end-tip,'faceplate_min_rotor_clearance':s.distance(motor),'hub_flange_radial_clearance':(p.bore_d-p.hub_flange_d)/2,'base_gap':a.distance(s),'faceplate_material_under_heads':g-seat,'hub_material_under_heads':p.hub_screw_seat},'hole_centers_world_mm':centers,'limitations':['Static nominal geometry. Actual printer accuracy, hardware tolerances, cable routing, hub retention and structural capacity require physical review.']}


def stl_info(path):
    raw=path.read_bytes(); n=struct.unpack_from('<I',raw,80)[0]
    need(len(raw)==84+50*n,'Expected binary STL')
    verts=[]; edges=Counter(); directed=Counter(); signed_volume=0
    for i in range(n):
        t=struct.unpack_from('<12fH',raw,84+50*i)[3:12]; v=[tuple(t[k:k+3]) for k in (0,3,6)]; verts+=v
        aa,bb,cc=v
        signed_volume+=(aa[0]*(bb[1]*cc[2]-bb[2]*cc[1])+aa[1]*(bb[2]*cc[0]-bb[0]*cc[2])+aa[2]*(bb[0]*cc[1]-bb[1]*cc[0]))/6
        for u,w in ((v[0],v[1]),(v[1],v[2]),(v[2],v[0])): edges[tuple(sorted((u,w)))]+=1; directed[(u,w)]+=1
    return {'bytes':len(raw),'triangles':n,'bounds_mm':[[min(v[i] for v in verts),max(v[i] for v in verts)] for i in range(3)],'closed_edges':all(c==2 for c in edges.values()),'consistent_winding':all(directed[(w,u)]==c for (u,w),c in directed.items()),'signed_volume_mm3':signed_volume,'sha256':hashlib.sha256(raw).hexdigest()}


def verify_vendor(p,parts,centers,folder,report):
    files=['EG17-G5.STEP','MJ5208.step','moteus_devkit_bracket.step']
    checks={}
    report['reference_hashes']={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in files}
    def read(name):
        return cq.importers.importStep(str(folder/name)).val()
    def rotate(shape):
        return shape.rotate((0,0,0),(1,0,0),90).rotate((0,0,0),(0,0,1),90)
    g=p.rotor_x+p.face_gap
    gear=[rotate(s).translate((g+4.25,2.08754633425126,p.axis_z-2.64671053092605)) for s in read(files[0]).Solids()]
    for i,solid in enumerate(gear):
        for name,part in parts.items():
            clear(part,solid,f'gear_{i}_{name}',checks)
    long_driver_hits={}
    for y,z in centers['flange']:
        # Conservative swept bound for a radial L-key handle turning +/-30 degrees.
        # A 4 mm diameter tube is enclosed by the offset sector extrusion.
        radial_y=y/math.hypot(y,z-p.axis_z)
        radial_z=(z-p.axis_z)/math.hypot(y,z-p.axis_z)
        vertices=[]
        for u,side in [(-2,-1),(42,-1),(42,1),(-2,1)]:
            v=side*(u*math.tan(math.pi/6)+2/math.cos(math.pi/6))
            vertices.append(cq.Vector(g+8+12-2,y+u*radial_y-v*radial_z,z+u*radial_z+v*radial_y))
        handle=cq.Solid.extrudeLinear(cq.Wire.makePolygon(vertices+[vertices[0]]),[],cq.Vector(7,0,0))
        for i,solid in enumerate(gear):
            blocked=volume_common(solid,cyl(g+8,y,z,2,25))
            if blocked>1e-6: long_driver_hits[f'body_{i}_{y}_{z}']=blocked
            for name,envelope in [('head',cyl(g+5,y,z,2.75,3)),('short_key_entry',cyl(g+8-2,y,z,2,17)),('key_handle_swing',handle),('head_insertion',cyl(g+5,y,z,2.75,13)),('shank',cyl(g+5-p.screw_length,y,z,1.5,p.screw_length))]:
                clear(solid,envelope,f'gear_{i}_{name}_{y}_{z}',checks)
    report['excluded_25mm_straight_driver_overlap_mm3']=long_driver_hits
    motor=read(files[1]).Solids()
    need(len(motor)==242,'Motor reference revision changed')
    for i in (237,238,239,240,241):
        body=rotate(motor[i]).translate((p.rotor_x-24.8,0,p.axis_z))
        for name,part in parts.items():
            clear(part,body,f'motor_{i}_{name}',checks)
    bracket=read(files[2]).rotate((0,0,0),(0,0,1),90).translate((0,0,p.axis_z))
    for name,part in parts.items():
        clear(part,bracket,'bracket_'+name,checks)
    for y,z in centers['bracket']:
        clear(bracket,cyl(p.cheek_x+p.cheek_depth,y,z,4,60),f'bracket_approach_{y}_{z}',checks)
    report['vendor_overlap_mm3']=checks

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--out',type=Path,default=Path('fitcheck_r03')); ap.add_argument('--params',type=Path); ap.add_argument('--references',type=Path); args=ap.parse_args()
    need(not args.out.exists(),'Output directory exists; choose a new revision/run folder')
    p=P()
    if args.params: p=replace(p,**json.loads(args.params.read_text()))
    for k,v in asdict(p).items(): need(isinstance(v,(int,float)) and math.isfinite(v),'Invalid parameter '+k)
    parts,centers=build(p); report=verify(p,parts,centers)
    args.out.mkdir(parents=True,exist_ok=False)
    for name,shape in parts.items():
        mesh=shape
        if name=='faceplate':
            # Gearbox-contact face flat on bed, recesses face upward.
            mesh=shape.translate((-(p.rotor_x+p.face_gap),0,-p.axis_z)).rotate((0,0,0),(0,1,0),90)
        if name=='hub_COMPANION_REQUIRED':
            mesh=shape.translate((-p.rotor_x,0,-p.axis_z)).rotate((0,0,0),(0,1,0),-90)
        stl=args.out/(name+'_r03_UNPOWERED.stl'); step=args.out/(name+'_r03_UNPOWERED.step')
        cq.exporters.export(mesh,str(stl),tolerance=p.mesh_linear,angularTolerance=p.mesh_angular)
        cq.exporters.export(shape,str(step))
        info=stl_info(stl); need(info['closed_edges'] and info['consistent_winding'] and info['signed_volume_mm3']>0,'STL validation failed: '+name)
        need(abs(info['signed_volume_mm3']-shape.Volume())/shape.Volume()<.002,'Mesh volume discrepancy')
        info.update({'brep_valid':shape.isValid(),'solid_count':len(shape.Solids()),'brep_volume_mm3':shape.Volume()}); report[name]=info
    assembly=cq.Assembly(name='UNPOWERED_r03_ENVELOPE_REVIEW')
    colors=[(.27,.52,.68),(.26,.60,.67),(.60,.64,.69),(.92,.57,.21)]
    for (name,shape),color in zip(parts.items(),colors):
        if name!='faceplate': assembly.add(shape,name=name,color=cq.Color(*color))
    motor=cyl(p.rotor_x-p.motor_body_length,0,p.axis_z,p.rotor_d/2,p.motor_body_length)
    assembly.add(motor,name='MOTOR_ENVELOPE_NOT_VENDOR_CAD',color=cq.Color(.5,.5,.5,.25))
    gearbox=box(p.rotor_x+p.face_gap,-21,p.axis_z-21,p.gearbox_body_length,42,42)
    assembly.add(gearbox,name='GEARBOX_EXTERNAL_ENVELOPE_NO_INTERNALS',color=cq.Color(.4,.45,.5,.15))
    assembly.export(str(args.out/'assembly_r03_ENVELOPE_REVIEW.step'))
    report.update({'status':'OFF-REPO candidate; PETG static fit-check only; NO powered or metal release','cadquery':cq.__version__,'python':platform.python_version(),'parameters':asdict(p),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    if args.references:
        verify_vendor(p,parts,centers,args.references,report)
    report['export_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(args.out.iterdir())}
    (args.out/'verification_r03.json').write_text(json.dumps(report,indent=2)+'\n')
    (args.out/'parameters_r03.json').write_text(json.dumps(asdict(p),indent=2)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(report['checks_overlap_mm3']),'datums_mm':report['datums_mm'],'parts':{k:report[k] for k in parts}},indent=2))
if __name__=='__main__': main()
