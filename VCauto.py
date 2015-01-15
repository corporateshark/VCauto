#! /usr/bin/python
#
# VCproj generator
# Version 0.7.00
# (15/01/2015)
# (C) Kosarevsky Sergey, 2005-2015
# support@linderdaum.com
# Part of Linderdaum Engine
# http://www.linderdaum.com

import os
import sys
import uuid
import codecs
import platform

VCAutoVersion = "0.7.00 (15/01/2015)"

Verbose = False

GenerateVCPROJ  = False
GenerateMAKE    = False
GenerateQT      = False
GenerateCB      = False
GenerateAndroid = False
RunBatchBuild   = ""

# default source dir
SourceDirs     = []

# default SDK path
SDKPath = os.path.join("..", "..")

# MSVC compiler configuration
OutputFileName           = "" # .vcproj or .vcxproj will be added automatically
ProjectName              = "" # must be supplied in command line

# platforms configuration
ConfigPath2010       = "ConfigVCAuto/ConfigurationX"
ConfigPath2012       = "ConfigVCAuto/ConfigurationX_2012"
ConfigPath2013       = "ConfigVCAuto/ConfigurationX_2013"
ConfigPathQtTarget   = "" # will be generated as: ProjectName+".pro"
ConfigPathCBTarget   = "" # will be generated as: ProjectName+".cbp", Code::Blocks
ConfigPathMAKETarget = "makefile"
ConfigPathMAKE       = os.path.join( sys.path[0], "Targets.list" )
# We use gcc to avoid C/C++ file problems
CompilerName         = "gcc"
ArName               = "ar"
ModuleName           = "" # must be supplied in command line or will be generated as: ProjectName+".exe"
MainCPPName          = "" # must be supplied in command line or will be generated as: ProjectName+".cpp"
ObjFilesList         = "obj_files"
IncludeDirsList      = "include_dirs"

# Qt configuration
DefaultQtEpilog      = ""
ConfigQtEpilog       = DefaultQtEpilog

# Code::Blocks configuration
ConfigCBProlog       = ""

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

VisualStudio2010 = False
VisualStudio2012 = False
VisualStudio2013 = False

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

def ClearAll():
   global OutputFileName
   global ProjectName
   global IncludeDirs
   global IncludeFiles
   global IncludeFilesDirs
   global SourceDirs
   global SourceFiles
   global SourceFilesDirs
   global ObjectFiles
   global ExcludeDirs
   global ExcludeFiles
   global ModuleName
   global MainCPPName
   global ConfigPathQtTarget
   global ConfigPathCBTarget
   OutputFileName = ""
   ProjectName    = ""
   SourceDirs   = []
   IncludeDirs  = []
   IncludeFiles = []
   IncludeFilesDirs = []
   SourceFiles  = []
   SourceFilesDirs  = []
   ObjectFiles  = []
   ExcludeDirs  = [".svn",".hg"]
   ExcludeFiles = []
   ModuleName   = ""
   MainCPPName  = ""
   ConfigPathQtTarget = ""
   ConfigPathCBTarget = ""

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
   print( "(C) Sergey Kosarevsky, 2005-2014. http://www.linderdaum.com" )
   print("")

def ShowHelp():
   print( r'''
Usage: VCauto.py [option <param>]

Available options:
   -s      - source directory
   -o      - output .vcproj/.vcxproj file name for MSVC (without extension)
   -ver    - target version of MSVC (2010, 2012 and 2013 are supported)
   -i      - additional include directory
   -c      - MSVC configuration file
   -m      - makefile configuration file
   -t      - ouput makefile name
   -qt     - Qt .pro epilog file name
   -andr1  - Android makefile prolog file name
   -andr2  - Android makefile epilog file name
   -k      - use Out/Obj for output instead of Out (this is used to compile engine's core)
   -cc     - GNU compiler name
   -ar     - GNU archiver name
   -b      - run specified batch script (overrides all other command line options)
   -plex   - list of platform-specific excludes
   -exlist - list of excluded files
   -exdirlist - list of excluded directories
   -ex     - exclude directory from project (can repeat)
   -exf    - exclude file from project (can repeat)
   -olist  - temporary output list of object files (default: obj_files)
   -ilist  - temporary output list of include dirs (default: include_dirs)
   -pr     - project name''' )
   sys.exit(0)

def CheckArgs( i, argv, Message ):
   if i >= len(argv):
      print( Message )
      sys.exit(255)
   return argv[i]

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

def LoadExcludesList( ExcludesFileName ):
   global ExcludeFiles
   for Line in open( ExcludesFileName ).readlines():
      ExcludeFiles.append( str.strip( Line ) )

def LoadExcludeDirsList( ExcludeDirsFileName ):
   global ExcludeDirs
   for Line in open( ExcludeDirsFileName ).readlines():
      ExcludeDirs.append( str.strip( Line ) )

def ParseCommandLine(argv, BatchBuild):
   global OutputFileName
   global VisualStudio2010
   global VisualStudio2012
   global VisualStudio2013
   global SourceDirs
   global ConfigPath2010
   global ConfigPath2012
   global ConfigPath2013
   global IncludeDirs
   global ConfigPathMAKE
   global ConfigPathMAKETarget
   global ConfigPathQtTarget
   global ConfigPathCBTarget
   global ConfigQtEpilog
   global ConfigCBProlog
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
   global GenerateCB
   global GenerateAndroid
   global GeneratingCore
   global Verbose
   global RunBatchBuild
   global ObjFilesList
   global IncludeDirsList
   argc = len(argv)
   for i in range(1, argc, 2):
      OptionName = CheckArgs( i, argv, "Option name expected" )
      OptionValue = CheckArgs( i+1, argv, "Option value expected" )
      if OptionName == "-v" or OptionName == "--verbose": Verbose = True
      elif OptionName == "-s" or OptionName == "--source-dir": SourceDirs.append( CheckArgs( i+1, argv, "Directory name expected for option -s" ) )
      elif OptionName == "-o" or OptionName == "--output-file-MSVC": OutputFileName = CheckArgs( i+1, argv, "File name expected for option -o" )
      elif OptionName == "-ver" or OptionName == "--MSVC-version":
         GenerateVCPROJ = True
         CompilerVer = CheckArgs( i+1, argv, "MSVC version expected for option -ver" )
			# convert Compiler ver, if needed
         if CompilerVer == "2010":
            VisualStudio2010 = True
         elif CompilerVer == "2012":
            VisualStudio2012 = True
         elif CompilerVer == "2013":
            VisualStudio2013 = True
      elif OptionName == "-i" or OptionName == "--include-dir": IncludeDirs.append( CheckArgs( i+1, argv, "Directory name expected for option -i" ) )
      elif OptionName == "-c" or OptionName == "--MSVC-config":
         ConfigPath = CheckArgs( i+1, argv, "File name expected for option -c" )
         ConfigPath2010 = ConfigPath + "X";
         ConfigPath2012 = ConfigPath + "X_2012";
         ConfigPath2013 = ConfigPath + "X_2013";
      elif OptionName == "-m" or OptionName == "--makefile-config": ConfigPathMAKE = CheckArgs( i+1, argv, "File name expected for option -m" )
      elif OptionName == "-t" or OptionName == "--makefile-target": 
         ConfigPathMAKETarget = CheckArgs( i+1, argv, "File name expected for option -t" )
         GenerateMAKE = True
      elif OptionName == "-cc" or OptionName == "--compiler-name" : CompilerName = CheckArgs( i+1, argv, "File name expected for option -cc" )
      elif OptionName == "-ar" or OptionName == "--ar-name"       : ArName = CheckArgs( i+1, argv, "File name expected for option -ar" )
      elif OptionName == "-ex" or OptionName == "--exclude-dir"   : ExcludeDirs.append( CheckArgs( i+1, argv, "Directory name expected for option -ex" ) )
      elif OptionName == "-exf" or OptionName == "--exclude-file" : ExcludeFiles.append( CheckArgs( i+1, argv, "File name expected for option -exf" ) )
      elif OptionName == "-pr" or OptionName == "--project-name"  : ProjectName = CheckArgs( i+1, argv, "Project name expected for option -pr" )
      elif OptionName == "-b" or OptionName == "--batch-build"    : RunBatchBuild = CheckArgs( i+1, argv, "Expected batch build file name for option -b" )
      elif OptionName == "-plex" or OptionName == "--platforms-excludes" : LoadPlatformsExcludes( CheckArgs( i+1, argv, "Expected excludes filename for option -plex" ) )
      elif OptionName == "-exlist" or OptionName == "--exclude-list" : LoadExcludesList( CheckArgs( i+1, argv, "Expected excludes filename for option -exlist" ) )
      elif OptionName == "-exdirlist" or OptionName == "--exclude-dirs-list" : LoadExcludeDirsList( CheckArgs( i+1, argv, "Expected excludes filename for option -exdirlist" ) )
      elif OptionName == "-olist" : ObjFilesList = CheckArgs( i+1, argv, "Expected file name for option -olist" )
      elif OptionName == "-ilist" : IncludeDirsList = CheckArgs( i+1, argv, "Expected file name for option -ilist" )
      elif OptionName == "-qt" or OptionName == "--qt-epilog"     : 
         ConfigQtEpilog = CheckArgs( i+1, argv, "Epilog file name expected for option -qt" )
         GenerateQT = True
      elif OptionName == "-cbp" or OptionName == "--cbp-prologue" :
         ConfigCBProlog = CheckArgs( i+1, argv, "Prologue file name expected for option -cbp" )
         GenerateCB = True
      elif OptionName == "-andr1" or OptionName == "--android-prolog"     : ConfigAndroidProlog = CheckArgs( i+1, argv, "Epilog file name expected for option -andr1" )
      elif OptionName == "-andr2" or OptionName == "--android-epilog"     : ConfigAndroidEpilog = CheckArgs( i+1, argv, "Epilog file name expected for option -andr2" )
      elif OptionName == "-androut" or OptionName == "--android-out":
         ConfigPathAndroidTarget = CheckArgs( i+1, argv, "Output .mk file name expected for option -androut" )
         GenerateAndroid = True
      elif OptionName == "-k"  or OptionName == "--core"          :
         DEFAULT_OBJ_DIR = CORE_OBJ_DIR
         GeneratingCore = True
      else: CheckArgs( 0, [], "Invalid option: " + OptionName )
   if ( not ProjectName and not RunBatchBuild ) and BatchBuild:
      print( "A valid project name must be specified with -pr option" )
      sys.exit( 255 )
   if not ModuleName:
      ModuleName = ProjectName + ".exe"

   if len(SourceDirs) == 0: SourceDirs.append( "Src" )
   if not MainCPPName: MainCPPName = os.path.join( SourceDirs[0], ProjectName + ".cpp" )
   if not OutputFileName: OutputFileName = ProjectName
   if not ConfigPathQtTarget: ConfigPathQtTarget = ProjectName + ".pro"
   if not ConfigPathCBTarget: ConfigPathCBTarget = ProjectName + ".cbp"

def ReplacePatterns(Text):
   Text = Text.replace( PATTERN_PROJECT_NAME,  ProjectName )
   Text = Text.replace( PATTERN_PROJECT_GUID,  str.upper(str(uuid.uuid5(uuid.NAMESPACE_URL, ProjectName))) )
   Text = Text.replace( PATTERN_MODULE_NAME,   ModuleName  )
   Text = Text.replace( PATTERN_MAIN_CPP_NAME, MainCPPName )
   Text = Text.replace( PATTERN_SDK_PATH,      SDKPath )
   return Text

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

def GenerateAll():
   if Verbose: print( "Project name:", ProjectName)

   for SourceDir in SourceDirs:
      IncludeDirs.append( SourceDir )

      # create VC config
      if Verbose: print( "Reading directory tree from: ", SourceDir )

      Scan( SourceDir )

   if Verbose: print( "Reading make config from:", ConfigPathMAKE )
   if VisualStudio2010:
      if Verbose: print( "Reading MSVC config from:", ConfigPath2010 )
   if VisualStudio2012:
      if Verbose: print( "Reading MSVC config from:", ConfigPath2012 )
   if VisualStudio2013:
      if Verbose: print( "Reading MSVC config from:", ConfigPath2013 )
   if Verbose: print("")

   if GenerateVCPROJ and (VisualStudio2010 or VisualStudio2012 or VisualStudio2013):
      FileName = OutputFileName + ".vcxproj"
      if Verbose: print( "Generating: ", FileName )
      Out = open( FileName, 'wb' )
      Out.write( codecs.BOM_UTF8 )
      Out.close()
      Out = open( FileName, 'a' )
      # copy Configuration. template
      if VisualStudio2010:
         tmpl = open( ConfigPath2010 ).read()
      elif VisualStudio2012:
         tmpl = open( ConfigPath2012 ).read()
      else:
         tmpl = open( ConfigPath2013 ).read()
      Out.write( ReplacePatterns( tmpl ) )
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
      Out.write( "\n# User-defined preamble\n\n" )
      Out.write( ReplacePathSepUNIX( ReplacePatterns( open( ConfigPathMAKE+".preamble" ).read() ) ) )

      ObjDir = DEFAULT_OBJ_DIR

      # 2. Include directories
      IncDirList = open( IncludeDirsList, "w")

      Out.write( INCLUDE_DIRS_STRING + " = " + "-I . \\\n" )

      for Name in IncludeDirs:
         Out.write( MultiTab(1) + "-I " + ReplacePathSepUNIX(Name) + " \\\n" );
         IncDirList.write("-I " + ReplacePathSepUNIX(Name) + " ")

      IncDirList.close()

      Out.write("\n\n# iOS SDK's GCC4.0 does not support compressed command line, at least not in an obvious way\n")

      Out.write("ifdef IOS_BUILD\n")

      Out.write("\nCOPTS = $(INCLUDE_DIRS) \n\n")

      Out.write("# Normal GCC compilers go here\n")

      Out.write("else\n")

      Out.write( "\nCOPTS = " )
   #   Out.write( "$(" + INCLUDE_DIRS_STRING + ")" + "\n\n" )
      Out.write( " @" +IncludeDirsList+ " \n" )

      Out.write("\nendif\n")

      # 3. list of object files
      Out.write( "\n# Object files list\n" )
      Out.write( OBJS_STRING + " = " + " \\\n" )

      ObjFileList = open( ObjFilesList, "w" )

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
         # -MD option is not used right now, but it slows down the compilation
         Line = MultiTab(1) + "$(CC) $(COPTS) -c " + ReplacePathSepUNIX(SourceFiles[Index]) + " -o $(OBJDIR)/" + ReplacePathSepUNIX(Name) + " $(CFLAGS)";
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

   # 9. Generate .cbp Code::Blocks project
   if GenerateCB:
      if Verbose: print( "Generating: ", ConfigPathCBTarget )
      Out = open( ConfigPathCBTarget, 'w' )

      if len(ConfigCBProlog) > 0:
         Out.write( ReplacePathSepUNIX( ReplacePatterns( open( ConfigCBProlog ).read() ) ) )

      for Index, Name in enumerate(ObjectFiles):
         if SourceFiles[Index].endswith(".c"):
            Out.write( "		<Unit filename=\"" + ReplacePathSepUNIX(SourceFiles[Index]) + "\">\n" )
            Out.write( "			<Option compilerVar=\"CC\" />\n" )
            Out.write( "		</Unit>\n" )
         else:
            Out.write( "		<Unit filename=\"" + ReplacePathSepUNIX(SourceFiles[Index]) + "\" />\n" )

      Out.write( "	</Project>\n" )
      Out.write( "</CodeBlocks_project_file>\n" )
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

# 
# MAIN
#

if os.getenv("LSDK_PATH") is not None: SDKPath = ReplacePathSep( os.getenv("LSDK_PATH") )

if Verbose: ShowLogo()

if len(sys.argv) < 2:
	if not Verbose: ShowLogo()
	ShowHelp()

ParseCommandLine(sys.argv, True)

if ( not RunBatchBuild ):
   # just run and exit
   GenerateAll()
else:
   # process all commands
   print( "Running batch script:", RunBatchBuild )
   OldDir = os.getcwd()
   for Line in open( RunBatchBuild ).readlines():
      Command = Line.split();
      print( "Working path :", Command[0] )
      ClearAll()
      ParseCommandLine( Command, False )
      os.chdir( Command[0] )
      GenerateAll()
      os.chdir( OldDir )
