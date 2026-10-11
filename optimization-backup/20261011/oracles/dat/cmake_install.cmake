# Install script for directory: /puffertank/pufferlib/vendor/fast-nle/dat

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/root/nethackdir.nle/nhdat;/root/nethackdir.nle/perm;/root/nethackdir.nle/record;/root/nethackdir.nle/logfile;/root/nethackdir.nle/xlogfile")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/root/nethackdir.nle" TYPE FILE MESSAGE_LAZY FILES
    "/puffertank/pufferlib/vendor/fast-nle/build/dat/nhdat"
    "/puffertank/pufferlib/vendor/fast-nle/build/dat/perm"
    "/puffertank/pufferlib/vendor/fast-nle/build/dat/record"
    "/puffertank/pufferlib/vendor/fast-nle/build/dat/logfile"
    "/puffertank/pufferlib/vendor/fast-nle/build/dat/xlogfile"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/root/nethackdir.nle/dat/help;/root/nethackdir.nle/dat/hh;/root/nethackdir.nle/dat/cmdhelp;/root/nethackdir.nle/dat/keyhelp;/root/nethackdir.nle/dat/history;/root/nethackdir.nle/dat/opthelp;/root/nethackdir.nle/dat/wizhelp;/root/nethackdir.nle/dat/bigroom.des;/root/nethackdir.nle/dat/castle.des;/root/nethackdir.nle/dat/endgame.des;/root/nethackdir.nle/dat/gehennom.des;/root/nethackdir.nle/dat/knox.des;/root/nethackdir.nle/dat/medusa.des;/root/nethackdir.nle/dat/mines.des;/root/nethackdir.nle/dat/oracle.des;/root/nethackdir.nle/dat/sokoban.des;/root/nethackdir.nle/dat/tower.des;/root/nethackdir.nle/dat/yendor.des;/root/nethackdir.nle/dat/Arch.des;/root/nethackdir.nle/dat/Barb.des;/root/nethackdir.nle/dat/Caveman.des;/root/nethackdir.nle/dat/Healer.des;/root/nethackdir.nle/dat/Knight.des;/root/nethackdir.nle/dat/Monk.des;/root/nethackdir.nle/dat/Priest.des;/root/nethackdir.nle/dat/Ranger.des;/root/nethackdir.nle/dat/Rogue.des;/root/nethackdir.nle/dat/Samurai.des;/root/nethackdir.nle/dat/Tourist.des;/root/nethackdir.nle/dat/Valkyrie.des;/root/nethackdir.nle/dat/Wizard.des;/root/nethackdir.nle/dat/bogusmon.txt;/root/nethackdir.nle/dat/data.base;/root/nethackdir.nle/dat/dungeon.def;/root/nethackdir.nle/dat/engrave.txt;/root/nethackdir.nle/dat/epitaph.txt;/root/nethackdir.nle/dat/oracles.txt;/root/nethackdir.nle/dat/quest.txt;/root/nethackdir.nle/dat/rumors.fal;/root/nethackdir.nle/dat/rumors.tru;/root/nethackdir.nle/dat/tribute;/root/nethackdir.nle/dat/license;/root/nethackdir.nle/dat/symbols")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/root/nethackdir.nle/dat" TYPE FILE MESSAGE_LAZY FILES
    "/puffertank/pufferlib/vendor/fast-nle/dat/help"
    "/puffertank/pufferlib/vendor/fast-nle/dat/hh"
    "/puffertank/pufferlib/vendor/fast-nle/dat/cmdhelp"
    "/puffertank/pufferlib/vendor/fast-nle/dat/keyhelp"
    "/puffertank/pufferlib/vendor/fast-nle/dat/history"
    "/puffertank/pufferlib/vendor/fast-nle/dat/opthelp"
    "/puffertank/pufferlib/vendor/fast-nle/dat/wizhelp"
    "/puffertank/pufferlib/vendor/fast-nle/dat/bigroom.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/castle.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/endgame.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/gehennom.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/knox.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/medusa.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/mines.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/oracle.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/sokoban.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/tower.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/yendor.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Arch.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Barb.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Caveman.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Healer.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Knight.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Monk.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Priest.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Ranger.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Rogue.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Samurai.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Tourist.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Valkyrie.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/Wizard.des"
    "/puffertank/pufferlib/vendor/fast-nle/dat/bogusmon.txt"
    "/puffertank/pufferlib/vendor/fast-nle/dat/data.base"
    "/puffertank/pufferlib/vendor/fast-nle/dat/dungeon.def"
    "/puffertank/pufferlib/vendor/fast-nle/dat/engrave.txt"
    "/puffertank/pufferlib/vendor/fast-nle/dat/epitaph.txt"
    "/puffertank/pufferlib/vendor/fast-nle/dat/oracles.txt"
    "/puffertank/pufferlib/vendor/fast-nle/dat/quest.txt"
    "/puffertank/pufferlib/vendor/fast-nle/dat/rumors.fal"
    "/puffertank/pufferlib/vendor/fast-nle/dat/rumors.tru"
    "/puffertank/pufferlib/vendor/fast-nle/dat/tribute"
    "/puffertank/pufferlib/vendor/fast-nle/dat/license"
    "/puffertank/pufferlib/vendor/fast-nle/dat/symbols"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/root/nethackdir.nle/save/")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  file(INSTALL DESTINATION "/root/nethackdir.nle/save" TYPE DIRECTORY MESSAGE_LAZY FILES "")
endif()

