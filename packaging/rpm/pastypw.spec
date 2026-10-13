# PastyNew Password Generator - RPM spec
#
# Built automatically by .github/workflows/build.yml on Fedora, and locally
# with:   rpmbuild -ba packaging/rpm/pastypw.spec
#
%global appname pastypw
%global version 1.0.0
%global release 1

Name:           %{appname}
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        Offline password generator with a modern dark interface

License:        MIT
URL:            https://github.com/PastyNew/pastypw
Source0:        %{name}-%{version}.tar.gz

# The application ships its own Qt6 runtime, so library auto-detection would
# only add unsatisfiable dependencies on systems without Qt installed.
AutoReqProv: disable
AutoReq: disable

%global debug_package %{nil}

BuildArch:      x86_64
Requires:       glibc
Requires:       libGL
Requires:       libEGL
Requires:       libxkbcommon
Requires:       fontconfig
Requires:       dbus-libs
Requires:       libX11
Requires:       libXext

# Qt6 runtime libraries
Requires:       libxcb
Requires:       libxcb-cursor
Requires:       libxcb-icccm
Requires:       libxcb-image
Requires:       libxcb-keysyms
Requires:       libxcb-render-util
Requires:       libxcb-shape
Requires:       libxcb-xinerama
Requires:       libxcb-xkb
Requires:       libxcb-sync
Requires:       libxcb-randr
Requires:       libxcb-xfixes

%description
PastyNew Password Generator is a small, fast and completely offline password
generator with a modern dark interface.

Features:
* cryptographically secure randomness (OS CSPRNG via Python secrets)
* length from 4 to 64 characters, digits / letters / symbols on demand
* batch generation of up to 50 unique passwords at once
* entropy and crack-time estimate for every password
* local history with favourites and export to .txt
* Russian and English interface, no network access, no telemetry

%prep
%autosetup

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libdir}/%{appname}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
mkdir -p %{buildroot}%{_datadir}/doc/%{appname}

# The PyInstaller bundle ships in dist/pastypw (see scripts/build_rpm.sh)
cp -a dist/pastypw/. %{buildroot}%{_libdir}/%{appname}/
rm -f %{buildroot}%{_libdir}/%{appname}/*.spec

# The launcher resolves its own directory instead of hardcoding %{_libdir},
# because Fedora uses /usr/lib64 while other distributions use /usr/lib.
cat > %{buildroot}%{_bindir}/%{appname} <<'EOF'
#!/bin/sh
# PastyNew Password Generator launcher
self=$(readlink -f "$0")
dir=$(dirname "$self")
for candidate in \
    "$dir/../lib64/pastypw/pastypw" \
    "$dir/../lib/pastypw/pastypw" \
    "$dir/../libexec/pastypw/pastypw"
do
    if [ -x "$candidate" ]; then
        exec "$candidate" "$@"
    fi
done
echo "pastypw: application files not found" >&2
exit 1
EOF
chmod 755 %{buildroot}%{_bindir}/%{appname}

install -m 0644 packaging/desktop/%{appname}.desktop \
    %{buildroot}%{_datadir}/applications/%{appname}.desktop
install -m 0644 build/icons/%{appname}-256.png \
    %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/%{appname}.png
install -m 0644 build/icons/%{appname}.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/%{appname}.svg

%files
%license LICENSE
%{_bindir}/%{appname}
%{_libdir}/%{appname}
%{_datadir}/applications/%{appname}.desktop
%{_datadir}/icons/hicolor/256x256/apps/%{appname}.png
%{_datadir}/icons/hicolor/scalable/apps/%{appname}.svg
%doc README.md README.en.md CHANGELOG.md

%changelog
* Tue Oct 13 2026 PastyNew <pastypew@gmail.com> - 1.0.0-1
- Initial release: PastyNew Password Generator by PastyNew