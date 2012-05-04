#! /usr/bin/python
#
# VCproj generator
# Version 0.6.11
# (16/04/2012)
# (C) Kosarevsky Sergey, 2005-2012
# support@linderdaum.com
# Part of Linderdaum Engine
# http://www.linderdaum.com

import os
import sys
import uuid
import codecs
import platform

VCAutoVersion = "0.6.11 (16/04/2012)"

Verbose = False

GenerateVCPROJ  = False
GenerateMAKE    = False
GenerateQT      = False
GenerateAndroid = False

# default source dir
SourceDir     = "Src"

# default SDK path
SDKPath = os.path.join("..", "..")

# MSVC compiler configuration
OutputFileName           = "" # .vcproj or .vcxproj will be added automatically
ProjectName              = "" # must be supplied in command line

# platforms configuration
ConfigPath2008       = "ConfigVCAuto/Configuration"
ConfigPath2010       = "ConfigVCAuto/Configuration.X"
ConfigPathQtTarget   = "" # will be generated as: ProjectName+".pro"
ConfigPathMAKETarget = "makefile"
ConfigPathMAKE       = os.path.join( sys.path[0], "Targets.list" )
# We use gcc to avoid C/C++ file problems
CompilerName         = "gcc"
ArName               = "ar"
ModuleName           = "" # must be supplied in command line or will be generated as: ProjectName+".exe"
MainCPPName          = "" # must be supplied in command line or will be generated as: ProjectName+".cpp"

# Qt configuration
DefaultQtEpilog      = ""
ConfigQtEpilog       = DefaultQtEpilog

# Android configuration
ConfigPathAndroidTarget = "Android.mk"
DefaultAndroidProlog    = ""
DefaultAndroidEpilog    = ""
ConfigAndroidProlog     = DefaultAndroidProlog
ConfigAndroidEpilog     = DefaultAndroidEpilog

# list of excluded files for different targets
ExcludeFilesVS        = []
ExcludeFilesQt        = []
ExcludeFilesMake      = []
ExcludeFilesAndroid   = []

##############################

DEFAULT_OBJECT_FILE_EXTENSION = ".o"
INCLUDE_DIRS_STRING           = "INCLUDE_DIRS"
OBJS_STRING                   = "OBJS"
DEFAULT_OBJ_DIR               = "Obj"
CORE_OBJ_DIR                  = "Out/Obj"

PATTERN_PROJECT_NAME  = "<!PROJECT_NAME!>"
PATTERN_PROJECT_GUID  = "<!PROJECT_GUID!>"
PATTERN_MODULE_NAME   = "<!MODULE_NAME!>"
PATTERN_MAIN_CPP_NAME = "<!MAIN_CPP_NAME!>"
PATTERN_SDK_PATH      = "<!LSDK_PATH!>"



###############################################
###############################################
###############################################
#########         VCauto          #############
###############################################
###############################################
###############################################

VisualStudio2008 = False
VisualStudio2010 = False

# declare collections
IncludeDirs  = []
IncludeFiles = []
IncludeFilesDirs = []
SourceFiles  = []
SourceFilesDirs  = []
ObjectFiles  = []
ExcludeDirs  = [".svn"]
ExcludeFiles = []

# hack
GeneratingCore = False

def IsHeaderFile(FileName):
   if FileName.endswith(".h"): return True
   if FileName.endswith(".hh"): return True
   if FileName.endswith(".hxx"): return True
   if FileName.endswith(".hpp"): return True
   return False;

def IsSourceFile(FileName):
   if FileName.endswith(".cpp"): return True
   if FileName.endswith(".cxx"): return True
   if FileName.endswith(".c")  : return True
   if FileName.endswith(".cc") : return True
   return False

def IsCPPFile(FileName):
   if FileName.endswith(".cpp"): return True
   if FileName.endswith(".cxx"): return True
   return False

def MakeObjectFile(FileName):
   Pos = -1
   if Pos == -1: Pos = FileName.rfind(".cpp")
   if Pos == -1: Pos = FileName.rfind(".cxx")
   if Pos == -1: Pos = FileName.rfind(".c")
   if Pos == -1: Pos = FileName.rfind(".cc")
   if Pos == -1: return ""
   return FileName[0:Pos:] + ".o"

def MakeHeaderFile(FileName):
   Pos = -1
   if Pos == -1: Pos = FileName.rfind(".cpp")
   if Pos == -1: Pos = FileName.rfind(".cxx")
   if Pos == -1: Pos = FileName.rfind(".c")
   if Pos == -1: Pos = FileName.rfind(".cc")
   if Pos == -1: return ""
   return FileName[0:Pos:] + ".h"

def MultiTab(Count):
   Result = ""
   for i in range(0, Count): Result += "\t"
   return Result

def ReplacePathSep(File):  
   CleanPath = str.replace( File, "\\", os.path.sep )
   CleanPath = str.replace( CleanPath, "/", os.path.sep )
   return CleanPath

def ReplacePathSepUNIX(File):  
   return str.replace( File, "\\", "/" )

#def MakeConfigPath(FileName):
#   Name = FileName
#   Pos = Name.find( "vcauto.exe" )
#   return FileName[0:Pos]

def ShowLogo():
   print("")
   print( "VCauto autobuilder. Version", VCAutoVersion )
   print( "(C) Sergey Kosarevsky, 2005-2011. http://www.linderdaum.com" )
   print("")

def ShowHelp():
   print( r'''
Usage: VCauto.py [option <param>]

Available options:
   -s     - source directory
   -o     - output .vcproj/.vcxproj file name for MSVC (without extension)
   -ver   - target version of MSVC (2008 and 2010 are supported)
   -i     - additional include directory
   -c     - MSVC configuration file
   -m     - makefile configuration file
   -t     - ouput makefile name
   -qt    - Qt .pro epilog file name
   -andr1 - Android makefile prolog file name
   -andr2 - Android makefile epilog file name
   -k     - use Out/Obj for output instead of Out (this is used to compile engine's core)
   -cc    - GNU compiler name
   -ar    - GNU archiver name
   -ex    - exclude directory from project (can repeat)
   -exf   - exclude file from project (can repeat)
   -pr    - project name''' )
   sys.exit(0)

def CheckArgs( i, NumArgs, Message ):
   if i >= NumArgs:
      print( Message )
      sys.exit(255)
   return sys.argv[i]

def LoadPlatformsExcludes( ExcludesFileName ):
   global ExcludeFilesVS
   global ExcludeFilesQt
   global ExcludeFilesMake
   global ExcludeFilesAndroid
   for Line in open( ExcludesFileName ).readlines():
      Platform = str.strip( Line[ :Line.find(':'): ] )
      FileName = ReplacePathSep( str.strip( Line[  Line.find(':')+1:: ] ) )
      print( "'"+Platform+"'   '"+FileName+"'" )
      if Platform == "VS": ExcludeFilesVS.append( FileName )
      elif Platform == "QT": ExcludeFilesQt.append( FileName )
      elif Platform == "MAKE": ExcludeFilesMake.append( FileName )
      elif Platform == "ANDROID": ExcludeFilesAndroid.append( FileName )
  
def ParseCommandLine():
   global OutputFileName
   global VisualStudio2008
   global VisualStudio2010
   global SourceDir
   global ConfigPath2008
   global ConfigPath2010
   global IncludeDirs
   global ConfigPathMAKE
   global ConfigPathMAKETarget
   global ConfigPathQtTarget
   global ConfigQtEpilog
   global ConfigAndroidProlog
   global ConfigAndroidEpilog
   global ConfigPathAndroidTarget
   global CompilerName
   global ArNam
   global ExcludeDirs
   global ExcludeFiles
   global ProjectName
   global ModuleName
   global MainCPPName
   global DEFAULT_OBJ_DIR
   global GenerateVCPROJ
   global GenerateMAKE
   global GenerateQT
   global GenerateAndroid
   global GeneratingCore
   global Verbose
   argc = len(sys.argv)
   for i in range(1, argc, 2):
      OptionName = sys.argv[i]
      OptionValue = sys.argv[i+1]
      if OptionName == "-v" or OptionName == "--verbose": Verbose = True
      if OptionName == "-s" or OptionName == "--source-dir": SourceDir = CheckArgs( i+1, argc, "Directory name expected for option -s" )
      elif OptionName == "-o" or OptionName == "--output-file-MSVC": OutputFileName = CheckArgs( i+1, argc, "File name expected for option -o" )
      elif OptionName == "-ver" or OptionName == "--MSVC-version":
         GenerateVCPROJ = True
         CompilerVer = CheckArgs( i+1, argc, "MSVC version expected for option -ver" )
			# convert Compiler ver, if needed
         if CompilerVer == "2008":
            VisualStudio2008 = True
         elif CompilerVer == "2010":
            VisualStudio2010 = True
      elif OptionName == "-i" or OptionName == "--include-dir": IncludeDirs.append( CheckArgs( i+1, argc, "Directory name expected for option -i" ) )
      elif OptionName == "-c" or OptionName == "--MSVC-config":
         ConfigPath2008 = CheckArgs( i+1, argc, "File name expected for option -c" )
         # FIXME: its a dirty hack
         if (platform.system() == "Windows"):
            ConfigPath2010 = ConfigPath2008 + "X";
         else:
            ConfigPath2010 = ConfigPath2008 + ".X";

      elif OptionName == "-m" or OptionName == "--makefile-config": ConfigPathMAKE = CheckArgs( i+1, argc, "File name expected for option -m" )
      elif OptionName == "-t" or OptionName == "--makefile-target": 
         ConfigPathMAKETarget = CheckArgs( i+1, argc, "File name expected for option -t" )
         GenerateMAKE = True
      elif OptionName == "-cc" or OptionName == "--compiler-name" : CompilerName = CheckArgs( i+1, argc, "File name expected for option -cc" )
      elif OptionName == "-ar" or OptionName == "--ar-name"       : ArName = CheckArgs( i+1, argc, "File name expected for option -ar" )
      elif OptionName == "-ex" or OptionName == "--exclude-dir"   : ExcludeDirs.append( CheckArgs( i+1, argc, "Directory name expected for option -ex" ) )
      elif OptionName == "-exf" or OptionName == "--exclude-file" : ExcludeFiles.append( CheckArgs( i+1, argc, "File name expected for option -exf" ) )
      elif OptionName == "-pr" or OptionName == "--project-name"  : ProjectName = CheckArgs( i+1, argc, "Project name expected for option -pr" )
      elif OptionName == "-plex" or OptionName == "--platforms-excludes" : LoadPlatformsExcludes( CheckArgs( i+1, argc, "Expected excludes filename for option -plex" ) )
      elif OptionName == "-qt" or OptionName == "--qt-epilog"     : 
         ConfigQtEpilog = CheckArgs( i+1, argc, "Epilog file name expected for option -qt" )
         GenerateQT = True
      elif OptionName == "-andr1" or OptionName == "--android-prolog"     : ConfigAndroidProlog = CheckArgs( i+1, argc, "Epilog file name expected for option -andr1" )
      elif OptionName == "-andr2" or OptionName == "--android-epilog"     : ConfigAndroidEpilog = CheckArgs( i+1, argc, "Epilog file name expected for option -andr2" )
      elif OptionName == "-androut" or OptionName == "--android-out":
         ConfigPathAndroidTarget = CheckArgs( i+1, argc, "Output .mk file name expected for option -androut" )
         GenerateAndroid = True
      elif OptionName == "-k"  or OptionName == "--core"          :
         DEFAULT_OBJ_DIR = CORE_OBJ_DIR
         GeneratingCore = True
      else: CheckArgs( 0, 0, "Invalid option: " + OptionName )
   if not ProjectName:
      print( "A valid project name must be specified with -pr option" )
      sys.exit( 255 )
   if not ModuleName:  ModuleName = ProjectName + ".exe"
   if not MainCPPName: MainCPPName = os.path.join( SourceDir, ProjectName + ".cpp" )
   if not OutputFileName: OutputFileName = ProjectName
   if not ConfigPathQtTarget: ConfigPathQtTarget = ProjectName + ".pro"

def ReplacePatterns(Text):
   Text = Text.replace( PATTERN_PROJECT_NAME,  ProjectName )
   Text = Text.replace( PATTERN_PROJECT_GUID,  str.upper(str(uuid.uuid5(uuid.NAMESPACE_URL, ProjectName))) )
   Text = Text.replace( PATTERN_MODULE_NAME,   ModuleName  )
   Text = Text.replace( PATTERN_MAIN_CPP_NAME, MainCPPName )
   Text = Text.replace( PATTERN_SDK_PATH,      SDKPath )
   return Text

def GenVC2008(NestLevel, Out, Path):
    for Item in os.listdir( Path ):
       ItemPath = os.path.join(Path, Item)
       if os.path.isdir(ItemPath): 
          if Item in ExcludeDirs: continue
          Out.write( MultiTab(NestLevel  ) + "<Filter\n" )
          Out.write( MultiTab(NestLevel+1) + "Name = \"" + Item + "\"\n" )
          Out.write( MultiTab(NestLevel+1) + "Filter = \"\">\n" )
          GenVC2008( NestLevel+1, Out, os.path.join( Path, Item ) )
          Out.write( MultiTab(NestLevel) + "</Filter>\n" )
       elif os.path.isfile(ItemPath): 
          if Item in ExcludeFiles: continue
          if Item in ExcludeFilesVS: continue
          OmitDot = Item.find("..") != -1;
          Out.write( MultiTab(NestLevel  ) + "<File\n" )
          Out.write( MultiTab(NestLevel+1) + "RelativePath=" + "\"" + ( "" if OmitDot else ".\\" ) + os.path.join( Path, Item ) + "\">\n" )
          Out.write( MultiTab(NestLevel  ) + "</File>\n" )

# prepare directory structure
def Scan(Path):
    for Item in os.listdir( Path ):
       ItemPath = os.path.join(Path, Item)
       if os.path.isdir(ItemPath): 
          if Item in ExcludeDirs: continue
          CleanPath = str.replace( ItemPath, "\\", os.path.sep )
          CleanPath = str.replace( CleanPath, "/", os.path.sep )
          IncludeDirs.append( CleanPath )
          Scan( os.path.join( Path, Item ) )
       elif os.path.isfile( ItemPath ): 
          if Item in ExcludeFiles: continue
          if IsHeaderFile( Item ): 
             IncludeFiles.append( ItemPath )
             IncludeFilesDirs.append( Path )
          elif IsSourceFile( ItemPath ):
             SourceFiles.append( ItemPath )
             SourceFilesDirs.append( Path )
             ObjectFiles.append( MakeObjectFile( Item ) )

# 
# MAIN
#

if os.getenv("LSDK_PATH") is not None: SDKPath = ReplacePathSep( os.getenv("LSDK_PATH") )

if Verbose: ShowLogo()

if len(sys.argv) < 2:
	if not Verbose: ShowLogo()
	ShowHelp()

ParseCommandLine()

if Verbose: print( "Project name:", ProjectName)

IncludeDirs.append( SourceDir )

# create VC config
if Verbose: print( "Reading directory tree from: ", SourceDir )

Scan( SourceDir )

if Verbose: print( "Reading make config from:", ConfigPathMAKE )
if VisualStudio2008:
   if Verbose: print( "Reading MSVC config from:", ConfigPath2008 )
if VisualStudio2010:
   if Verbose: print( "Reading MSVC config from:", ConfigPath2010 )
if Verbose: print("")

if GenerateVCPROJ and VisualStudio2008:
   FileName = OutputFileName + ".vcproj"
   if Verbose: print( "Generating: ", FileName )
   Out = open( FileName, 'wb' )
   Out.close()
   Out = open( FileName, 'a' )
   Out.write( "<?xml version=\"1.0\" encoding=\"windows-1251\"?>\n" )
   Out.write( "<VisualStudioProject\n" )
   Out.write( MultiTab(1) + "ProjectType=\"Visual C++\"\n" )
   Out.write( MultiTab(1) + "Version=\"9,00\"\n" )
   # copy Configuration. template
   RealConf2008 = ConfigPath2008
#   if(platform.system() == "Windows")
#      RealConf2008 = ConfigPath.substr()

   Out.write( ReplacePatterns( open( RealConf2008 ).read() ) )
   # write files header
   Out.write( "\n" + MultiTab(1) + "<Files>\n" )
   Out.write( MultiTab(2) + "<Filter\n" )
   Out.write( MultiTab(3) + "Name=\"Source Files\"\n" )
   Out.write( MultiTab(3) + "UniqueIdentifier=\"{" + str.upper(str(uuid.uuid5(uuid.NAMESPACE_URL, ProjectName))) + "}\">\n" )
   # generate VC2008 output
   GenVC2008( 3, Out, SourceDir )
   Out.write( MultiTab(2) + "</Filter>\n" )
   Out.write( MultiTab(1) + "</Files>\n" )
   Out.write( "</VisualStudioProject>\n" )
   Out.close()

if GenerateVCPROJ and VisualStudio2010:
   FileName = OutputFileName + ".vcxproj"
   if Verbose: print( "Generating: ", FileName )
   Out = open( FileName, 'wb' )
   Out.write( codecs.BOM_UTF8 )
   Out.close()
   Out = open( FileName, 'a' )
   # copy Configuration. template
   Out.write( ReplacePatterns( open( ConfigPath2010 ).read() ) )
   # source files       
   Out.write( MultiTab(1) + "<ItemGroup>\n" )
   for File in SourceFiles: Out.write( MultiTab(2) + "<ClCompile Include= \"" + ReplacePathSep(File) + "\" />\n" )
   Out.write( MultiTab(1) + "</ItemGroup>\n" )
   # header files
   Out.write( MultiTab(1) + "<ItemGroup>\n" )
   for File in IncludeFiles: Out.write( MultiTab(2) + "<ClInclude Include= \"" + ReplacePathSep(File) + "\" />\n" )
   Out.write( MultiTab(1) + "</ItemGroup>\n" )
   # footer
   Out.write( MultiTab(1) + "<Import Project=\"$(VCTargetsPath)\\Microsoft.Cpp.targets\" />\n" )
   Out.write( MultiTab(1) + "<ImportGroup Label=\"ExtensionTargets\">\n" )
   Out.write( MultiTab(1) + "</ImportGroup>\n" )
   Out.write( "</Project>\n" )
   # filters
   OutF = open( FileName + ".filters", 'wb' )
   OutF.write( codecs.BOM_UTF8 )
   OutF.close()
   OutF = open( FileName + ".filters", 'a' )
   OutF.write( "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" )
   OutF.write( "<Project ToolsVersion=\"4.0\" xmlns=\"http://schemas.microsoft.com/developer/msbuild/2003\">\n" )
   OutF.write( MultiTab(1) + "<ItemGroup>\n" )
   for Dir in IncludeDirs:
      if Dir.find("..") == 0: continue
      OutF.write( MultiTab(2) + "<Filter Include=\"" + Dir + "\">\n" )
      OutF.write( MultiTab(3) + "<UniqueIdentifier>{" + str(uuid.uuid4()) + "}</UniqueIdentifier>\n" )
      OutF.write( MultiTab(2) + "</Filter>\n" )
   OutF.write( MultiTab(1) + "</ItemGroup>\n" );

   OutF.write( MultiTab(1) + "<ItemGroup>\n" )
   for Index, File in enumerate(SourceFiles):
      if File in ExcludeFilesVS: continue
      OutF.write( MultiTab(2) + "<ClCompile Include=\"" + File + "\">\n" )
      OutF.write( MultiTab(3) + "<Filter>" + SourceFilesDirs[Index] + "</Filter>\n" )
      OutF.write( MultiTab(2) + "</ClCompile>\n" )
   OutF.write( MultiTab(1) + "</ItemGroup>\n" )

   OutF.write( MultiTab(1) + "<ItemGroup>\n" )
   for Index, File in enumerate(IncludeFiles):
      if File in ExcludeFilesVS: continue
      OutF.write( MultiTab(2) + "<ClInclude Include=\"" + File + "\">\n" )
      OutF.write( MultiTab(3) + "<Filter>" + IncludeFilesDirs[Index] + "</Filter>\n" )
      OutF.write( MultiTab(2) + "</ClInclude>\n" )
   OutF.write( MultiTab(1) + "</ItemGroup>\n" )

   OutF.write( "</Project>" )
   OutF.close()
   Out.close()

# generate GNU output

if GenerateMAKE:
   if Verbose: print( "Generating: ", ConfigPathMAKETarget )
   Out = open( ConfigPathMAKETarget, 'w' )

   # 0. "symbolic" header
   Out.write( "# Autogenerated via VCauto " + VCAutoVersion + "\n\n" )

   # 1. Common stuff like compiler names etc.
   Out.write( "# Common defines" + "\n" )
   Out.write( "CC = " + CompilerName + "\n\n" )
   Out.write( "AR = " + ArName + "\n\n" )
   Out.write( "CFLAGS = " + "\n\n" )
   Out.write( "CPPFLAGS = " + "\n\n" )
   Out.write( "OBJDIR = " + DEFAULT_OBJ_DIR + "\n\n" )
   Out.write( "# Include directories\n" )

   ObjDir = DEFAULT_OBJ_DIR

   # 2. Include directories
   IncDirList = open("include_dirs", "w")

   Out.write( INCLUDE_DIRS_STRING + " = " + "-I . \\\n" )

   for Name in IncludeDirs:
      Out.write( MultiTab(1) + "-I " + ReplacePathSepUNIX(Name) + " \\\n" );
      IncDirList.write("-I " + ReplacePathSepUNIX(Name) + " ")

   IncDirList.close()

   Out.write( "\nCOPTS = " )
#   Out.write( "$(" + INCLUDE_DIRS_STRING + ")" + "\n\n" )
   Out.write( " @include_dirs\n " )

   # 3. list of object files
   Out.write( "\n# Object files list\n" )
   Out.write( OBJS_STRING + " = " + " \\\n" )

   ObjFileList = open("obj_files", "w")

   for Name in ObjectFiles:
      if Name in ExcludeFilesMake: continue
      Out.write( MultiTab(1) + "$(OBJDIR)/" + ReplacePathSepUNIX(Name) + " \\\n" );
      ObjFileList.write(ObjDir + "/" + ReplacePathSepUNIX(Name) + " ")

   ObjFileList.close()

   # 4. Object file compilation targets
   Out.write( "\n# Object files\n\n" )

   for Index, Name in enumerate(ObjectFiles):
      if Name in ExcludeFilesMake: continue
      Out.write( "$(OBJDIR)/" + ReplacePathSepUNIX(Name) + ": " + ReplacePathSepUNIX(SourceFiles[Index]) );
      DepHeader = ReplacePathSepUNIX(MakeHeaderFile(SourceFiles[Index]))
      if os.path.exists( DepHeader ):
         Out.write( " " + DepHeader + "\n" )
      else:
         Out.write( "\n" )
      Line = MultiTab(1) + "$(CC) $(COPTS) -MD -c " + ReplacePathSepUNIX(SourceFiles[Index]) + " -o $(OBJDIR)/" + ReplacePathSepUNIX(Name) + " $(CFLAGS)";
      if IsCPPFile( SourceFiles[Index] ):
         Out.write( Line + " $(CPPFLAGS)\n\n" )
      else:
         Out.write( Line + "\n\n" )

   # 5. Targets > take them from Targets.list
   Out.write( "\n# User-defined targets\n\n" )
   Out.write( ReplacePathSepUNIX( ReplacePatterns( open( ConfigPathMAKE ).read() ) ) )

   # 6. End of makefile
   Out.write( "\n\n# End of Makefile\n" )

# 7. Generate .pro Qt-project
if GenerateQT:
   if Verbose: print( "Generating: ", ConfigPathQtTarget )
   Out = open( ConfigPathQtTarget, 'w' )
   Out.write( "#\n" )
   Out.write( "# Qt-project created by VCauto " + VCAutoVersion + "\n" )
   Out.write( "#\n" )
   Out.write( "\n" )

   for File in IncludeFiles: 
      Out.write( "HEADERS += " + ReplacePathSepUNIX(File) + "\n" )

   Out.write( "\n" )

   for Index, Name in enumerate(ObjectFiles):
      if Name in ExcludeFilesQt: continue
      Out.write( "SOURCES += " + ReplacePathSepUNIX(SourceFiles[Index]) + "\n" )

   # 8. Add Qt epilog
   if len(ConfigQtEpilog) > 0:
      Out.write( ReplacePathSepUNIX( ReplacePatterns( open( ConfigQtEpilog ).read() ) ) )

   Out.close()

# 9. Generate Android project
if GenerateAndroid:
   if Verbose: print( "Generating: ", ConfigPathAndroidTarget )

   try:
      Out = open( ConfigPathAndroidTarget, 'w' )

      # 10. Add Android prolog
      if len(ConfigAndroidProlog) > 0:
         Out.write( ReplacePatterns( open( ConfigAndroidProlog ).read() ) )

      Out.write( "\n" )

      # 11. Include directories
      Out.write( "LOCAL_C_INCLUDES += \\\n" )

      Prefix = "../";

      if GeneratingCore: Prefix = "../../";

      for Name in IncludeDirs:
         Out.write( MultiTab(1) + "$(LOCAL_PATH)/" + Prefix + ReplacePathSepUNIX(Name) + " \\\n" );

      Out.write( "\n" )
      Out.write( "LOCAL_SRC_FILES += \\\n" )

      for Name in SourceFiles:
         if Name in ExcludeFilesAndroid: 
            if Verbose: print( "   Android excluded:", Name )
            continue
         Out.write( MultiTab(1) + Prefix + ReplacePathSepUNIX(Name) + " \\\n" );

      Out.write( "\n" )

      # 12. Add Android epilog
      if len(ConfigAndroidEpilog) > 0:
         Out.write( ReplacePathSepUNIX( ReplacePatterns( open( ConfigAndroidEpilog ).read() ) ) )

      Out.close()
   except IOError:
      if Verbose: print( "Cannot open: ", ConfigPathAndroidTarget, " --- skipping" )
     