import 'package:flutter/material.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    const darkBlue = Color(0xFF0D2B45);

    return Drawer(
      backgroundColor: Colors.white,
      child: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.fromLTRB(
                20,
                28,
                20,
                24,
              ),
              color: darkBlue,
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundColor: Colors.white,
                    child: Icon(
                      Icons.person,
                      size: 34,
                      color: darkBlue,
                    ),
                  ),

                  SizedBox(height: 15),

                  Text(
                    'MarkScan AI',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 21,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  SizedBox(height: 4),

                  Text(
                    'Faculty Dashboard',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 12),

            _drawerItem(
              context,
              icon: Icons.home_outlined,
              title: 'Home',
              iconColor: darkBlue,
              onTap: () {
                Navigator.pop(context);
              },
            ),

            _drawerItem(
              context,
              icon: Icons.camera_alt_outlined,
              title: 'Enter Marks',
              iconColor: darkBlue,
              onTap: () {
                Navigator.pop(context);
              },
            ),

            _drawerItem(
              context,
              icon: Icons.assignment_outlined,
              title: 'Manage Marks',
              iconColor: darkBlue,
              onTap: () {
                Navigator.pop(context);
              },
            ),

            _drawerItem(
              context,
              icon: Icons.settings_outlined,
              title: 'Settings',
              iconColor: darkBlue,
              onTap: () {
                Navigator.pop(context);
              },
            ),

            const Spacer(),

            const Divider(height: 1),

            _drawerItem(
              context,
              icon: Icons.logout_outlined,
              title: 'Logout',
              iconColor: darkBlue,
              onTap: () {
                Navigator.pop(context);
              },
            ),

            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }

  Widget _drawerItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    required Color iconColor,
    required VoidCallback onTap,
  }) {
    const lightBlue = Color(0xFFE8EEF5);

    return ListTile(
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: 20,
        vertical: 3,
      ),
      leading: Container(
        width: 42,
        height: 42,
        decoration: BoxDecoration(
          color: lightBlue,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(
          icon,
          color: iconColor,
        ),
      ),
      title: Text(
        title,
        style: const TextStyle(
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}