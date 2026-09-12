import styles from "./app-sibar.module.css";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import {
  Mail,
  Calendar,
  HardDrive,
  FileText,
  Sparkles,
  Link,
} from "lucide-react";

export function AppSidebar() {
  return (
    <Sidebar className={styles.customSidebar}>
      <SidebarHeader className={styles.header}>
        <div className={styles.logoBadge}>LinGo</div>
        <span className={styles.headerTitle}></span>
      </SidebarHeader>

      <SidebarContent>
        <div className={styles.activeAiButton}>
          <Sparkles className={styles.sparkleIcon} size={18} />
          <span>
            <a href="/home">Home</a>
          </span>
        </div>

        {/* Список пунктов навигации */}
        <SidebarMenu className={styles.menuList}>
          <SidebarMenuItem>
            <SidebarMenuButton className={styles.menuButton}>
              <Mail size={18} />
              <span>
                <a href="/chat">Chat</a>
              </span>
            </SidebarMenuButton>
          </SidebarMenuItem>

          <SidebarMenuItem>
            <SidebarMenuButton className={styles.menuButton}>
              <Calendar size={18} />
              <span>
                <a href="/profile">Profile</a>
              </span>
            </SidebarMenuButton>
          </SidebarMenuItem>

          <SidebarMenuItem>
            <SidebarMenuButton className={styles.menuButton}>
              <HardDrive size={18} />
              <span>
                <a href="/progress">Progress</a>
              </span>
            </SidebarMenuButton>
          </SidebarMenuItem>

          <SidebarMenuItem>
            <SidebarMenuButton className={styles.menuButton}>
              <FileText size={18} />
              <span>
                <a href="/notes">Notes</a>
              </span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarContent>

      <SidebarFooter className={styles.footer}>
        <div className={styles.userCard}>
          <img
            src="https://api.dicebear.com/7.x/bottts/svg?seed=Dastan"
            alt="Avatar"
            className={styles.avatar}
          />
          <div className={styles.userInfo}>
            <span className={styles.userName}>Elhan</span>
            <span className={styles.userEmail}>elahn@gmail.com</span>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
