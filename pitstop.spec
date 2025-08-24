Name:           pitstop
Version:        1.0.0
Release:        3%{?dist}
Summary:        Car Parts and Service Management Application
License:        MIT
Group:          Applications/Productivity
URL:            https://msprimes.com/pitstop
Source0:        pitstop.py
Source1:        pitstop
Source2:        pitstop.desktop
Source3:        README.md

BuildArch:      noarch

BuildRequires:  python3-devel
Requires:       python3
Requires:       python3-tkinter
#Requires:       python3-ttkbootstrap

%description
PitStop is a Python-based GUI application for managing car parts, vehicles, service records, and service types. It uses a SQLite database to store data and provides a user-friendly interface with features like searching, sorting, CSV export, and overdue service highlighting.

%prep
%setup -q -c -T
cp %{SOURCE0} .
cp %{SOURCE1} .
cp %{SOURCE2} .
cp %{SOURCE3} .

%build
# No build step required for Python script

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/pitstop
mkdir -p %{buildroot}%{_localstatedir}/lib/pitstop
mkdir -p %{buildroot}%{_datadir}/applications

install -m 644 pitstop.py %{buildroot}%{_datadir}/pitstop/pitstop.py
install -m 755 pitstop %{buildroot}%{_bindir}/pitstop
install -m 644 pitstop.desktop %{buildroot}%{_datadir}/applications/pitstop.desktop

# Validate desktop file
desktop-file-validate %{buildroot}%{_datadir}/applications/pitstop.desktop

%files
%{_bindir}/pitstop
%{_datadir}/pitstop/pitstop.py
%{_datadir}/applications/pitstop.desktop
%doc README.md

%post

# Update desktop database
update-desktop-database &>/dev/null || :

%postun
# Update desktop database after uninstall
update-desktop-database &>/dev/null || :

%changelog
* Sun Aug 24 2025 Mladen Sekara <mladen.sekara@msprimes.com> - 1.0.0-3
- Moved database to user homedir
* Sun Aug 24 2025 Mladen Sekara <mladen.sekara@msprimes.com> - 1.0.0-2
- Minor bug fixes and upgrade to handle same part numbers across multiple vehicles
* Sat Aug 23 2025 Mladen Sekara <mladen.sekara@msprimes.com> - 1.0.0-1
- Initial package release
