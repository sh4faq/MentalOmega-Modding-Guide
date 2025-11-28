# INI Configuration Reference

This guide covers configuring custom units in Mental Omega using INI files.

## Mental Omega INI Structure

Mental Omega's core rules are in protected MIX files. To add custom units, use:

```
Mental Omega/INI/Map Code/Standard.ini
```

This file is loaded for all game modes and allows custom unit definitions.

---

## Complete Unit Example: Nexus Devastator

```ini
; ===============================================
; CUSTOM UNIT: Nexus Devastator (FTNKNEXUS)
; ===============================================

; Register the unit in VehicleTypes list
[VehicleTypes]
85=FTNKNEXUS

; Register custom warhead
[Warheads]
106=NexusPlasmaWH

; Define the warhead
[NexusPlasmaWH]
Verses=100%,100%,100%,100%,100%,100%,100%,100%,100%,100%,100%
CellSpread=0.5
PercentAtMax=1
InfDeath=2
AnimList=TWLT070,TWLT070
Wall=yes
Wood=yes
Sparky=yes

; Define the weapon
[NexusPlasmaCannon]
Damage=1000
ROF=120
Range=8
Speed=100
Warhead=NexusPlasmaWH
Report=GenericTankRpt
Projectile=InvisibleLow
Bright=yes
IsLaser=yes
LaserInnerColor=0,255,200
LaserOuterColor=0,128,100
LaserOuterSpread=0,0,0

; Define the unit
[FTNKNEXUS]
Image=FTNKNEXUS
UIName=Name:FTNKNEXUS
Name=Nexus Devastator
Category=AFV
Prerequisite=
Primary=NexusPlasmaCannon
TechLevel=1
Cost=1500
Soylent=750
Speed=6
Sight=8
Owner=Europeans,UnitedStates,Pacific,USSR,Latin,Chinese,PsiCorps,Headquaters,ScorpionCell
Strength=800
Armor=heavy
ROT=8
Turret=yes
TurretAnim=FTNKNEXUSTUR
Crusher=yes
Trainable=yes
Explodes=yes
DeathWeapon=UnitDeathWeapon
MovementZone=Normal
SpeedType=Track
Locomotor={4A582741-9839-11d1-B709-00A024DDAFD1}
IsTilter=yes
TooBigToFitUnderBridge=true
IsSelectableCombatant=yes
CrateGoodie=no
Points=25
VoiceSelect=RottweilerSelect
VoiceMove=RottweilerMove
VoiceAttack=RottweilerAttackCommand
DieSound=GenVehicleDie
CrushSound=TankCrush
MinDebris=1
MaxDebris=3
AllowedToStartInMultiplayer=yes
Voxel=yes
Remapable=yes
UseBuffer=yes
PrimaryFireFLH=150,0,180
Cameo=HTNKICNH
AltCameo=HTNKICNH
```

---

## Key Unit Properties

### Identity

| Property | Description | Example |
|----------|-------------|---------|
| Image | VXL filename (no extension) | `Image=FTNKNEXUS` |
| UIName | String table reference | `UIName=Name:FTNKNEXUS` |
| Name | Display name | `Name=Nexus Devastator` |

### Combat Stats

| Property | Description | Example |
|----------|-------------|---------|
| Strength | Hit points | `Strength=800` |
| Armor | Armor type | `Armor=heavy` |
| Primary | Primary weapon | `Primary=NexusPlasmaCannon` |
| Secondary | Secondary weapon | `Secondary=MachineGun` |

### Movement

| Property | Description | Example |
|----------|-------------|---------|
| Speed | Movement speed | `Speed=6` |
| SpeedType | Movement type | `SpeedType=Track` |
| MovementZone | Terrain access | `MovementZone=Normal` |
| Locomotor | Movement behavior GUID | See Locomotors table |

### Visual

| Property | Description | Example |
|----------|-------------|---------|
| Voxel | Uses VXL model | `Voxel=yes` |
| Turret | Has rotating turret | `Turret=yes` |
| TurretAnim | Turret VXL name | `TurretAnim=FTNKNEXUSTUR` |
| Remapable | Uses team colors | `Remapable=yes` |
| Cameo | Build icon | `Cameo=HTNKICNH` |

### Production

| Property | Description | Example |
|----------|-------------|---------|
| Cost | Build cost | `Cost=1500` |
| TechLevel | Tech requirement | `TechLevel=1` |
| Prerequisite | Required buildings | `Prerequisite=GAWEAP` |
| Owner | Factions that can build | `Owner=Europeans,USSR` |

---

## Locomotor GUIDs

Common locomotors for different unit types:

| Type | GUID | Use For |
|------|------|---------|
| Drive | `{4A582741-9839-11d1-B709-00A024DDAFD1}` | Tanks, vehicles |
| Hover | `{4A582742-9839-11d1-B709-00A024DDAFD1}` | Hovercraft |
| Walk | `{4A582744-9839-11d1-B709-00A024DDAFD1}` | Infantry mechs |
| Fly | `{4A582746-9839-11d1-B709-00A024DDAFD1}` | Aircraft |
| Float | `{4A582747-9839-11d1-B709-00A024DDAFD1}` | Ships |

---

## Armor Types

| Type | Description |
|------|-------------|
| none | No armor |
| flak | Anti-air armor |
| plate | Infantry armor |
| light | Light vehicle armor |
| medium | Medium vehicle armor |
| heavy | Heavy vehicle armor |
| wood | Building/structure |
| steel | Hardened structure |
| concrete | Bunker/wall |
| special_1 | Special type 1 |
| special_2 | Special type 2 |

---

## Weapon Configuration

### Weapon Properties

```ini
[WeaponName]
Damage=100           ; Base damage
ROF=60               ; Rate of fire (frames between shots)
Range=7              ; Attack range in cells
Speed=100            ; Projectile speed
Warhead=WarheadName  ; Damage type
Projectile=ProjName  ; Projectile type
Report=SoundName     ; Firing sound
```

### Laser Weapon Properties

```ini
IsLaser=yes
LaserInnerColor=R,G,B      ; Center color (0-255)
LaserOuterColor=R,G,B      ; Edge color
LaserOuterSpread=R,G,B     ; Spread colors
LaserDuration=15           ; How long laser shows
```

### Warhead Properties

```ini
[WarheadName]
; Damage vs armor types (11 values for 11 armor types)
Verses=100%,100%,100%,100%,100%,100%,100%,100%,100%,100%,100%

CellSpread=0.5       ; Area of effect radius
PercentAtMax=1.0     ; Damage at edge of spread
InfDeath=2           ; Infantry death animation (1-10)
AnimList=ANIM1       ; Impact animation
Wall=yes             ; Damages walls
Wood=yes             ; Damages wood
```

---

## Owner Factions (Mental Omega)

```ini
; Allied
Owner=Europeans,UnitedStates,Pacific

; Soviet
Owner=USSR,Latin,Chinese

; Epsilon
Owner=PsiCorps,Headquaters,ScorpionCell

; All factions
Owner=Europeans,UnitedStates,Pacific,USSR,Latin,Chinese,PsiCorps,Headquaters,ScorpionCell
```

---

## Fire-From Location (FLH)

The `PrimaryFireFLH` property sets where projectiles spawn:

```ini
PrimaryFireFLH=X,Y,Z
```

- **X**: Forward/backward (positive = forward)
- **Y**: Left/right (positive = left)
- **Z**: Up/down (positive = up)

Values are in leptons (1 cell = 256 leptons).

Example for a tank cannon:
```ini
PrimaryFireFLH=150,0,180    ; Front center, elevated
```

---

## Turret Configuration

For units with rotating turrets:

```ini
Turret=yes                    ; Enable turret
TurretAnim=UNITNAMETUR        ; Turret VXL filename
ROT=8                         ; Rotation speed (frames per facing)
TurretOffset=0                ; Turret height offset
HasTurretTooltip=yes          ; Show turret in tooltip
```

The turret VXL must exist as:
- `UNITNAMETUR.vxl`
- `UNITNAMETUR.hva`

---

## Sound Configuration

```ini
VoiceSelect=SelectSound       ; When selected
VoiceMove=MoveSound           ; When ordered to move
VoiceAttack=AttackSound       ; When ordered to attack
VoiceFeedback=FeedbackSound   ; Response feedback
DieSound=DeathSound           ; Death sound
CrushSound=CrushSound         ; When crushing
```

---

## Debugging Tips

### Unit Not Appearing in Build Menu

1. Check `TechLevel` is set and not -1
2. Verify `Owner` includes the faction
3. Check `Prerequisite` buildings exist
4. Verify unit is registered in `[VehicleTypes]`

### Unit Invisible

1. Verify `Image` matches VXL filename
2. Check `Voxel=yes` is set
3. Verify VXL/HVA are in MIX file
4. Check VXL has valid dimensions (not 0x0x0)

### Turret Not Rotating

1. Verify `Turret=yes`
2. Check `TurretAnim` matches turret VXL name
3. Verify turret VXL/HVA exist and section names match
4. Check `ROT` value is reasonable (5-10)

### Weapon Not Firing

1. Verify weapon name matches `Primary=`
2. Check `Range` is > 0
3. Verify `Warhead` exists
4. Check `Projectile` type is valid

---

## Template: New Tank Unit

```ini
[VehicleTypes]
XX=YOURTANK

[YOURTANK]
Image=YOURTANK
UIName=Name:YOURTANK
Name=Your Tank Name
Category=AFV
Primary=YourWeapon
TechLevel=1
Cost=1000
Speed=6
Sight=7
Owner=Europeans
Strength=500
Armor=heavy
ROT=8
Turret=yes
TurretAnim=YOURTANKTUR
Crusher=yes
MovementZone=Normal
SpeedType=Track
Locomotor={4A582741-9839-11d1-B709-00A024DDAFD1}
Voxel=yes
Remapable=yes
Cameo=YOURTANKCAMEO
```
